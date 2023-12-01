"""The DB operations module."""

# pylint: disable=missing-function-docstring
# pylint: disable=no-member

from datetime import datetime, timedelta, timezone
import json
from typing import Optional
import uuid


from . import db_models as dbm
from . import models
from .models import (
    Task,
    TaskUpdateRequest,
    ServerStatus,
    TaskStates,
    TaskListResponse,
    HTCClusterStates,
    HTCCluster,
    HTCClusterStatus,
)


def get_default_task_id() -> str:
    """Get the default task ID"""

    with dbm.db_rlock:
        task_id = "default"
        db_task: Optional[dbm.Task] = dbm.Task.query.get(task_id)
        if db_task is None:
            # create default task
            db_task = dbm.Task(
                id=task_id,
                retries_left=0,
            )
            dbm.db.session.add(db_task)
            dbm.db.session.commit()
    return task_id


def post_task():
    return {}


def delete_task(task_id: str) -> bool:
    with dbm.db_rlock:
        db_task = dbm.Task.query.get(task_id)
        if db_task is None:
            return False
        for db_log_entry in db_task.log_entries:  # type: ignore
            dbm.db.session.delete(db_log_entry)
        dbm.db.session.delete(db_task)
        dbm.db.session.commit()
        return True


def get_status():
    with dbm.db_rlock:
        utcnow = datetime.now(timezone.utc)
        n_tasks_queued = dbm.Task.query.filter(
            dbm.Task.state == TaskStates.QUEUED
        ).count()
        n_tasks_submitted = dbm.Task.query.filter(
            dbm.Task.state == TaskStates.SUBMITTED
        ).count()
        n_tasks_completed = dbm.Task.query.filter(
            dbm.Task.state == TaskStates.COMPLETED
        ).count()
        n_tasks_completed_error = dbm.Task.query.filter(
            dbm.Task.state == TaskStates.COMPLETED_WITH_ERROR
        ).count()
        n_tasks_timed_out = dbm.Task.query.filter(
            dbm.Task.state == TaskStates.TIMED_OUT
        ).count()

        return ServerStatus(
            response_date=utcnow,
            n_tasks_queued=n_tasks_queued,
            n_tasks_submitted=n_tasks_submitted,
            n_tasks_completed=n_tasks_completed,
            n_tasks_completed_with_error=n_tasks_completed_error,
            n_tasks_timed_out=n_tasks_timed_out,
        )


def get_tasks_queued():
    with dbm.db_rlock:
        utcnow = datetime.now(timezone.utc)

        task_list = []
        db_tasks = dbm.Task.query.filter(dbm.Task.state.in_([TaskStates.QUEUED])).all()
        # db_tasks = dbm.Task.query.all()
        for _task in db_tasks:
            db_task: dbm.Task = _task
            if db_task.retries_left <= 0:  # type: ignore
                continue
            task_list.append(db_task.dump_obj())

    return TaskListResponse(utcnow, task_list)


def get_tasks_completed():
    with dbm.db_rlock:
        utcnow = datetime.now(timezone.utc)

        task_list = []
        db_tasks = dbm.Task.query.filter(dbm.Task.state == TaskStates.COMPLETED).all()
        for _task in db_tasks:
            db_task: dbm.Task = _task
            task_list.append(db_task.dump_obj())

    return TaskListResponse(utcnow, task_list)


def get_tasks_all():
    with dbm.db_rlock:
        utcnow = datetime.now(timezone.utc)

        task_list = []
        db_tasks = dbm.Task.query.all()
        for _task in db_tasks:
            db_task: dbm.Task = _task
            task_list.append(db_task.dump_obj())

    return TaskListResponse(response_date=utcnow, items=task_list)


def get_task_by_id(task_id: str) -> Optional[Task]:
    with dbm.db_rlock:
        db_task: dbm.Task = dbm.Task.query.get(task_id)
        if db_task is None:
            return None

        task = db_task.dump_obj()

    return task


def create_task(task: Task) -> Task:
    with dbm.db_rlock:
        if task.id is None:
            task.id = str(uuid.uuid4())
        db_task = dbm.Task(**dbm.Task.obj_to_db_dict(task))
        dbm.db.session.add(db_task)
        dbm.db.session.commit()
        task = db_task.dump_obj()

    return task


def update_task(task_id: str, task_update_request: TaskUpdateRequest) -> Optional[Task]:
    with dbm.db_rlock:
        db_task: Optional[dbm.Task] = dbm.Task.query.get(task_id)
        if db_task is None:
            return None

        task = Task()

        utcnow = datetime.now(timezone.utc)
        nullable = []

        if task_update_request.state is not None:
            task.state = task_update_request.state
            task.state_date = utcnow

        if task_update_request.retries_left is not None:
            task.retries_left = task_update_request.retries_left

        if task_update_request.cluster_id is not None:
            task.cluster_id = task_update_request.cluster_id
        elif task_update_request.reset_cluster_id:
            nullable.append("cluster_id")

        if task_update_request.proc_id is not None:
            task.proc_id = task_update_request.proc_id
        elif task_update_request.reset_proc_id:
            nullable.append("proc_id")

        if task_update_request.expiration_date is not None:
            task.expiration_date = task_update_request.expiration_date
        elif task_update_request.reset_expiration_date:
            nullable.append("expiration_date")

        db_task.update_from_obj(task, nullable)
        dbm.db.session.add(db_task)
        dbm.db.session.commit()

        return db_task.dump_obj()


def reset_expired_tasks():
    with dbm.db_rlock:
        db_tasks = dbm.Task.query.filter(dbm.Task.state == TaskStates.SUBMITTED).all()

        utcnow = datetime.now(timezone.utc)
        requeued_task_ids = []
        timed_out_task_ids = []
        tasks_updated_flag = False
        for _db_task in db_tasks:
            db_task: dbm.Task = _db_task
            if db_task.expiration_date > utcnow:  # type: ignore
                continue
            if db_task.retries_left > 0:  # type: ignore
                db_task.state = TaskStates.QUEUED
                requeued_task_ids.append(db_task.id)
            else:
                db_task.state = TaskStates.TIMED_OUT
                timed_out_task_ids.append(db_task.id)
            db_task.state_date = utcnow
            db_task.expiration_date = None
            dbm.db.session.add(db_task)
            tasks_updated_flag = True

        if tasks_updated_flag:
            dbm.db.session.commit()

        if len(requeued_task_ids) > 0:
            print(f"requeued tasks:\n{requeued_task_ids}")
        if len(timed_out_task_ids) > 0:
            print(f"timed out tasks:\n{timed_out_task_ids}")


def get_db_htc_cluster_by_id(cluster_id: int) -> Optional[dbm.HTCCluster]:
    with dbm.db_rlock:
        db_htc_cluster = dbm.HTCCluster.query.get(cluster_id)
    return db_htc_cluster


def get_or_create_db_htc_cluster_by_id(cluster_id: int) -> dbm.HTCCluster:
    with dbm.db_rlock:
        db_htc_cluster = dbm.HTCCluster.query.get(cluster_id)
        if db_htc_cluster is None:
            db_htc_cluster = dbm.HTCCluster(
                id=cluster_id,
                task_id="-",
                sub_params_json="{}",
                cluster_ad_json="{}",
                first_proc=0,
                num_procs=0,
            )
            dbm.db.session.add(db_htc_cluster)
            dbm.db.session.commit()
        return db_htc_cluster


def update_cluster_task(cluster_id: Optional[int]):
    with dbm.db_rlock:
        db_htc_cluster: Optional[dbm.HTCCluster] = dbm.HTCCluster.query.get(cluster_id)
        if db_htc_cluster is None:
            return False

        task_id = db_htc_cluster.task_id
        if task_id is None or task_id == "-":  # type: ignore
            return False
        db_task: Optional[dbm.Task] = dbm.Task.query.get(task_id)
        if db_task is None:
            return False

        if db_task.cluster_id == cluster_id:  # type: ignore
            return False

        utcnow = datetime.now(timezone.utc)
        db_task.state = TaskStates.SUBMITTED
        db_task.state_date = utcnow
        db_task.cluster_id = cluster_id
        db_task.retries_left = db_task.retries_left - 1
        db_task.expiration_date = utcnow + timedelta(seconds=2 * 60)
        dbm.db.session.add(db_task)
        dbm.db.session.commit()

        return True


def create_htc_cluster(new_htc_cluster: HTCCluster) -> HTCCluster:
    with dbm.db_rlock:
        db_htc_cluster: Optional[dbm.HTCCluster] = dbm.HTCCluster.query.get(
            new_htc_cluster.id
        )
        if db_htc_cluster is not None:
            return db_htc_cluster.dump_obj()

        print(f"request:\n{new_htc_cluster}")

        new_htc_cluster.creation_date = datetime.now(timezone.utc)

        if new_htc_cluster.sub_params is None:
            new_htc_cluster.sub_params = {}

        if new_htc_cluster.cluster_ad is None:
            new_htc_cluster.cluster_ad = {}

        if new_htc_cluster.status is None:
            procs = []
            if new_htc_cluster.num_procs > 0:  # type: ignore
                for index in range(new_htc_cluster.num_procs):  # type: ignore
                    procs.append(
                        {
                            "index": new_htc_cluster.first_proc + index,  # type: ignore
                            "state": -1,
                            "exit_code": None,
                        }
                    )
            new_htc_cluster.status = HTCClusterStatus(
                cluster_state=HTCClusterStates.CREATED, procs=procs
            )
            print(f"updated status:\n{new_htc_cluster.status}")

        print(f"updated request:\n{new_htc_cluster}")

        db_htc_cluster = dbm.HTCCluster(
            **dbm.HTCCluster.obj_to_db_dict(new_htc_cluster)
        )
        dbm.db.session.add(db_htc_cluster)
        dbm.db.session.commit()

        return db_htc_cluster.dump_obj()


def update_htc_cluster(
    cluster_id: int, upd_htc_cluster: HTCCluster
) -> Optional[HTCCluster]:
    with dbm.db_rlock:
        db_htc_cluster: Optional[dbm.HTCCluster] = dbm.HTCCluster.query.get(cluster_id)
        if db_htc_cluster is None:
            return None

        db_htc_cluster.update_from_obj(upd_htc_cluster)

        dbm.db.session.add(db_htc_cluster)
        dbm.db.session.commit()

        return db_htc_cluster.dump_obj()


def update_cluster_status(cluster_id: int, status: dict):
    with dbm.db_rlock:
        db_htc_cluster = get_or_create_db_htc_cluster_by_id(cluster_id)
        db_htc_cluster.status_json = json.dumps(status)
        dbm.db.session.add(db_htc_cluster)
        dbm.db.session.commit()


def on_cluster_completion(htc_cluster: models.HTCCluster):
    if not htc_cluster or not htc_cluster.task_id or htc_cluster.task_id == "-":
        return

    cluster_state = htc_cluster.status.cluster_state  # type: ignore

    with dbm.db_rlock:
        db_task: Optional[Task] = dbm.Task.query.get(htc_cluster.task_id)
        if db_task is None:
            return
        if db_task.state != TaskStates.SUBMITTED:
            return

        utcnow = datetime.now(timezone.utc)

        if cluster_state == HTCClusterStates.COMPLETED_OK:
            db_task.state = TaskStates.COMPLETED
            db_task.state_date = utcnow
        elif cluster_state == HTCClusterStates.COMPLETED_ERROR:
            db_task.state = TaskStates.COMPLETED_WITH_ERROR
            db_task.state_date = utcnow
        db_task.expiration_date = None
        dbm.db.session.add(db_task)
        dbm.db.session.commit()


def on_job_termination(htc_job_event: models.HTCJobEvent):
    if htc_job_event is None or htc_job_event.event_type != "JOB_TERMINATED":
        return

    cluster_id = htc_job_event.cluster_id
    proc_id = htc_job_event.proc_id
    details = htc_job_event.details
    exit_code = None
    if "TerminatedNormally" not in details or not details["TerminatedNormally"]:
        job_state = HTCClusterStates.COMPLETED_ERROR
    else:
        if "ReturnValue" not in details:
            job_state = HTCClusterStates.COMPLETED_ERROR
        elif details["ReturnValue"] != 0:
            job_state = HTCClusterStates.COMPLETED_ERROR
            exit_code = details["ReturnValue"]
        else:
            job_state = HTCClusterStates.COMPLETED_OK
            exit_code = details["ReturnValue"]

    db_htc_cluster = get_or_create_db_htc_cluster_by_id(cluster_id)
    proc_id_range = (
        db_htc_cluster.first_proc,
        db_htc_cluster.first_proc + db_htc_cluster.num_procs,  # type: ignore
    )
    if proc_id < proc_id_range[0] or proc_id >= proc_id_range[1]:  # type: ignore
        return

    htc_cluster = db_htc_cluster.dump_obj()
    status = htc_cluster.status
    if status is None:
        return

    if status.cluster_state not in [
        HTCClusterStates.CREATED,
        HTCClusterStates.EXECUTING,
    ]:
        return

    proc_status_updated = False
    for proc_status in status.procs:  # type: ignore
        if proc_status["index"] != proc_id:
            continue
        if proc_status["state"] == job_state:
            break

        proc_status["state"] = job_state
        proc_status["exit_code"] = exit_code
        proc_status_updated = True

    if proc_status_updated:
        n_ok = 0
        n_error = 0
        for proc_status in status.procs:  # type: ignore
            if proc_status["state"] == HTCClusterStates.COMPLETED_OK:
                n_ok += 1
            if proc_status["state"] == HTCClusterStates.COMPLETED_ERROR:
                n_error += 1
        cluster_state_updated = False
        if n_ok + n_error >= htc_cluster.num_procs:  # type: ignore
            if n_error > 0:
                status.cluster_state = HTCClusterStates.COMPLETED_ERROR
            else:
                status.cluster_state = HTCClusterStates.COMPLETED_OK
            cluster_state_updated = True

        db_htc_cluster.update_from_obj(HTCCluster(status=status))
        dbm.db.session.add(db_htc_cluster)
        dbm.db.session.commit()

        if cluster_state_updated:
            on_cluster_completion(db_htc_cluster.dump_obj())


def post_htc_job_event(new_log_entry: models.HTCJobEvent) -> models.HTCJobEvent:
    with dbm.db_rlock:
        entry_id = new_log_entry.gen_entry_id()
        db_htc_job_event: Optional[dbm.HTCJobEvent] = dbm.HTCJobEvent.query.get(
            entry_id
        )
        if db_htc_job_event is not None:
            return db_htc_job_event.dump_obj()

        new_log_entry.creation_date = datetime.now(timezone.utc)
        print(new_log_entry)
        db_htc_job_event = dbm.HTCJobEvent(
            **dbm.HTCJobEvent.obj_to_db_dict(new_log_entry)
        )
        dbm.db.session.add(db_htc_job_event)
        dbm.db.session.commit()

        if new_log_entry.event_type == "JOB_TERMINATED":
            # update cluster
            on_job_termination(db_htc_job_event.dump_obj())

        return db_htc_job_event.dump_obj()
