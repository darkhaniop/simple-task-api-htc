"""
HTCondor task tracking
"""

# pylint: disable=no-member

import dataclasses
from datetime import datetime, timezone
import json
import os
import random
import threading
import time
from typing import Optional


import htcondor


from ..common.models import HTCCluster, Task, HTCJobEvent, TaskStates
from ..common import db_models as dbm
from ..common import db_ops


@dataclasses.dataclass
class SubmitResult:
    """SubmitResult"""

    creation_date: datetime
    cluster_id: int
    cluster_ad: dict
    first_proc: int
    num_procs: int


def get_tasks_to_run():
    """Dummy get tasks to run"""
    return []


def htc_submit_task(task: Task) -> Optional[SubmitResult]:
    """HTCondor submit task"""
    try:
        submit = htcondor.Submit(task.sub_params)
        result = htcondor.Schedd().submit(submit)
    except htcondor.HTCondorException as e:
        print(e)
        return None

    sub_result = SubmitResult(
        creation_date=datetime.now(timezone.utc),
        cluster_id=result.cluster(),
        cluster_ad=json.loads(result.clusterad().printJson()),
        first_proc=result.first_proc(),
        num_procs=result.num_procs(),
    )
    return sub_result


class HTCTracker(threading.Thread):
    """HTCondor task tracker thread"""

    stop_event: threading.Event
    log_filename: str
    task_root_dir: str
    jel: htcondor.JobEventLog

    def __init__(self) -> None:
        super().__init__(daemon=False)
        self.stop_event = threading.Event()

    def init_app(self, log_filename: str, task_root_dir: str = "./taskroot") -> None:
        """
        Initializes the app variables.
        """

        self.task_root_dir = task_root_dir
        self.log_filename = log_filename  # f"{self.app.instance_path}/htc-log/0.log"

    def stop(self) -> None:
        """Request thread stop."""
        self.stop_event.set()

    def submit_task(self, task: Task) -> None:
        """Submit task to HTCondor"""
        inject_params = {"log": self.log_filename}
        initialdir = f"{self.task_root_dir}/{task.id}"
        try:
            os.makedirs(initialdir, exist_ok=True)
            inject_params["initialdir"] = initialdir
        except OSError:
            pass

        sub_params = {
            **inject_params,
            **task.sub_params,  # type: ignore
        }
        task.sub_params = sub_params
        sub_result = htc_submit_task(task)
        if sub_result is None:
            with dbm.db_rlock:
                db_task: Optional[dbm.Task] = dbm.Task.query.get(task.id)
                if db_task is None:
                    return
                db_task.state = TaskStates.COMPLETED_WITH_ERROR
                db_task.state_date = datetime.now(timezone.utc)
                dbm.db.session.add(db_task)
                dbm.db.session.commit()
            return

        htc_cluster = HTCCluster(
            id=sub_result.cluster_id,
            task_id=task.id,
            sub_params=task.sub_params,
            cluster_ad=sub_result.cluster_ad,
            first_proc=sub_result.first_proc,
            num_procs=sub_result.num_procs,
        )
        with dbm.job_state_lock:
            with dbm.db_rlock:
                htc_cluster = db_ops.create_htc_cluster(htc_cluster)
                db_ops.update_cluster_task(htc_cluster.id)  # type: ignore

    def check_for_new_tasks(self) -> None:
        """Check the DB for new tasks."""
        task_list_response = db_ops.get_tasks_queued()
        for task in task_list_response.items:
            self.submit_task(task)

    def process_job_events(self) -> None:
        """Process HTCondor job events and update the DB accordingly."""
        with dbm.job_state_lock:
            for event in self.jel.events(stop_after=0):
                details = {}
                for key, value in event.items():
                    details[key] = value
                htc_job_event = HTCJobEvent(
                    cluster_id=event.cluster,
                    proc_id=event.proc,
                    timestamp=event.timestamp,
                    event_type=str(event.type),
                    details=details,
                )
                db_ops.post_htc_job_event(htc_job_event)

    def run(self) -> None:
        try:
            os.makedirs(self.task_root_dir, exist_ok=True)
        except OSError:
            pass
        self.jel = htcondor.JobEventLog(self.log_filename)
        print("htc thread starting")
        interval = 11.5 + random.random()
        self.stop_event.clear()
        count_at = time.monotonic()
        while not self.stop_event.is_set():
            time.sleep(1)
            current_t = time.monotonic()
            if current_t > count_at:
                self.check_for_new_tasks()
                self.process_job_events()
                count_at = time.monotonic() + interval

        print("htc thread exiting")
