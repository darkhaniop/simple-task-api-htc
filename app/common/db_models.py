"""DB models"""

import dataclasses
from datetime import datetime
import json
import threading
from typing import Any, Optional


import sqlalchemy
from sqlalchemy.orm import DeclarativeBase, Session, relationship, Query, Mapped
from sqlalchemy.sql import func


from . import models


_global_dict = {}


class MyDeclarativeBaseClassProp:
    """Simplified @classproperty decorator

    See: SO: How to make a class property? https://stackoverflow.com/q/5189699
    """

    def __init__(self, f) -> None:
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)


class MyDeclarativeBase(DeclarativeBase):
    """My DeclarativeBase"""

    @MyDeclarativeBaseClassProp
    def query(cls) -> Query:  # pylint: disable=no-self-argument
        """entity-bound Query instance"""

        return _global_dict["db"].session.query(cls)  # type: ignore


class SQLAlchemy:
    """SQLAlchemy - class that provides an interface similar to the one from Flask-SQLAlchemy"""

    Model = MyDeclarativeBase
    Column = sqlalchemy.Column
    DateTime = sqlalchemy.DateTime
    Double = sqlalchemy.Double
    ForeignKey = sqlalchemy.ForeignKey
    Integer = sqlalchemy.Integer
    String = sqlalchemy.String
    Text = sqlalchemy.Text
    engine: sqlalchemy.Engine

    @property
    def session(self) -> Session:
        """sqla session"""
        return Session(self.engine)

    # session: Session

    def my_init(self, echo: bool=False):
        """sqla my_init"""

        self.engine = sqlalchemy.create_engine("sqlite:///stapi_htc.db", echo=echo)

    def my_close(self):
        """sqla my_close"""

        print("closing sqla")


db = SQLAlchemy()
db_rlock = threading.RLock()

_global_dict["db"] = db

job_state_lock = threading.Lock()


def db_date_to_str(db_datetime: Optional[datetime]) -> Optional[str]:
    """Convert only valid db_datetime to str, otherwise use None"""
    if db_datetime:
        return str(db_datetime)
    return None


def db_json_to_dict(db_json: Optional[str]) -> Optional[dict]:
    """Convert non-empty JSON string to an object, otherwise use None"""
    if db_json:
        return json.loads(db_json)
    return None


def dict_to_db_json(d: Optional[dict]) -> Optional[str]:
    """Convert (not None) dict to JSON string, otherwise use None"""
    if d:
        return json.dumps(d)
    return None


def del_nulls_if_not_nullable(d: dict, nullable: Optional[list] = None) -> None:
    """Delete non-nullable nulls from dict"""
    if nullable is None:
        nullable = []
    del_list = []
    for key, value in d.items():
        if value is None and value not in nullable:
            del_list.append(key)
    for key in del_list:
        del d[key]


class Task(db.Model):
    """Task model"""

    __tablename__ = "tasks"

    id = db.Column(db.String(32), primary_key=True)
    retries_left = db.Column(db.Integer)
    creation_date = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),  # pylint: disable=not-callable
    )
    sub_params_json = db.Column(db.Text())
    state = db.Column(db.Integer)
    state_date = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),  # pylint: disable=not-callable
    )
    cluster_id = db.Column(db.Integer)
    proc_id = db.Column(db.Integer)
    expiration_date = db.Column(db.DateTime(timezone=True))

    # log_entries = db.relationship("LogEntry2", back_populates="task")
    log_entries: Mapped[list["LogEntry2"]] = relationship(
        "LogEntry2", back_populates="task"
    )

    def __repr__(self):
        return f"<Task {self.id}>"

    def _dump_camelcase_dict(self) -> dict:
        return {
            "id": self.id,
            "creationDate": db_date_to_str(self.creation_date),  # type: ignore
            "subParams": db_json_to_dict(self.sub_params_json),  # type: ignore
            "state": self.state,
            "stateDate": db_date_to_str(self.state_date),  # type: ignore
            "retriesLeft": self.retries_left,
            "clusterId": self.cluster_id,
            "procId": self.proc_id,
            "expirationDate": db_date_to_str(self.expiration_date),  # type: ignore
        }

    def dump_obj(self) -> models.Task:
        """Dumps the DB entity as a Task python object"""
        task_schema = models.SchemaInstances.get_task_schema()
        return task_schema.load(self._dump_camelcase_dict())  # type: ignore

    @classmethod
    def obj_to_db_dict(cls, obj: models.Task, nullable: Optional[list] = None) -> dict:
        """Dump a Task python object as DB-mappable dict."""

        if nullable is None:
            nullable = []
        d = dataclasses.asdict(obj)
        del_list = []
        for key, value in d.items():
            if value is None and value not in nullable:
                del_list.append(key)
        for key in del_list:
            del d[key]
        if "sub_params" in d:
            del d["sub_params"]
            d["sub_params_json"] = dict_to_db_json(obj.sub_params)
        return d

    def update_from_obj(self, obj: models.Task, nullable: Optional[list] = None):
        """Update the db row object from the Task python object"""

        if nullable is None:
            nullable = []
        if obj.sub_params is not None or "sub_params" in nullable:
            self.sub_params_json = dict_to_db_json(obj.sub_params)
        if obj.state is not None or "state" in nullable:
            self.state = obj.state
        if obj.state_date is not None or "state_date" in nullable:
            self.state_date = obj.state_date
        if obj.retries_left is not None or "retries_left" in nullable:
            self.retries_left = obj.retries_left
        if obj.cluster_id is not None or "cluster_id" in nullable:
            self.cluster_id = obj.cluster_id
        if obj.proc_id is not None or "proc_id" in nullable:
            self.proc_id = obj.proc_id
        if obj.expiration_date is not None or "expiration_date" in nullable:
            self.expiration_date = obj.expiration_date


class LogEntry2(db.Model):
    # pylint: disable=too-few-public-methods
    """LogEntry2"""

    __tablename__ = "log_entries"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(32), db.ForeignKey("tasks.id"))
    cluster_id = db.Column(db.String(32))
    creation_date = db.Column(db.DateTime(timezone=True))

    # task = db.relationship("Task", back_populates="log_entries")
    task: Mapped["Task"] = relationship("Task", back_populates="log_entries")

    def __repr__(self):
        return f"<TaskLog {self.id} task_id={self.task_id}>"


class HTCCluster(db.Model):
    """HTC Cluster DB model"""

    __tablename__ = "htc_cluster"

    id = db.Column(db.Integer, primary_key=True)
    creation_date = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),  # pylint: disable=not-callable
    )
    task_id = db.Column(db.String(32))
    sub_params_json = db.Column(db.Text)
    cluster_ad_json = db.Column(db.Text)
    first_proc = db.Column(db.Integer)
    num_procs = db.Column(db.Integer)
    status_json = db.Column(db.Text)

    def _status_json_to_obj(self) -> Optional[models.HTCClusterStatus]:
        if self.status_json is None:
            return None
        status_partial = models.HTCClusterStatusPartial()
        return status_partial.loads(self.status_json)  # type: ignore

    @classmethod
    def _status_obj_to_json(
        cls, status: Optional[models.HTCClusterStatus]
    ) -> Optional[str]:
        if status is None:
            return None
        status_partial = models.HTCClusterStatusPartial()
        return status_partial.dumps(status)

    def _dump_camelcase_dict(self) -> dict:
        return {
            "id": self.id,
            "creationDate": db_date_to_str(self.creation_date),  # type: ignore
            "taskId": self.task_id,
            "subParams": db_json_to_dict(self.sub_params_json),  # type: ignore
            "clusterAd": db_json_to_dict(self.cluster_ad_json),  # type: ignore
            "firstProc": self.first_proc,
            "numProcs": self.num_procs,
            "status": self._status_json_to_obj(),
        }

    def dump_obj(self) -> models.HTCCluster:
        """Dump DB entity as HTCCluster python object"""
        return models.HTCCluster(
            id=self.id,  # type: ignore
            creation_date=self.creation_date,  # type: ignore
            task_id=self.task_id,  # type: ignore
            sub_params=db_json_to_dict(self.sub_params_json),  # type: ignore
            cluster_ad=db_json_to_dict(self.cluster_ad_json),  # type: ignore
            first_proc=self.first_proc,  # type: ignore
            num_procs=self.num_procs,  # type: ignore
            status=self._status_json_to_obj(),  # type: ignore
        )

    @classmethod
    def obj_to_db_dict(
        cls, obj: models.HTCCluster, nullable: Optional[list] = None
    ) -> dict:
        """Dump an HTCCluster python object as DB-mappable dict."""

        # if obj.status is not None:
        #    print(f"obj_to_db_dict: {obj.status}")
        #    obj.status = dataclasses.asdict(obj.status)
        d = dataclasses.asdict(dataclasses.replace(obj))
        del_nulls_if_not_nullable(d, nullable)

        if "sub_params" in d:
            del d["sub_params"]
            d["sub_params_json"] = dict_to_db_json(obj.sub_params)
        if "cluster_ad" in d:
            del d["cluster_ad"]
            d["cluster_ad_json"] = dict_to_db_json(obj.cluster_ad)
        if "status" in d:
            del d["status"]
            d["status_json"] = cls._status_obj_to_json(obj.status)
        return d

    def update_from_obj(self, obj: models.HTCCluster, nullable: Optional[list] = None):
        """Update the db row object from the HTCCluster python object"""

        if nullable is None:
            nullable = []
        if obj.task_id is not None or "task_id" in nullable:
            self.task_id = obj.task_id
        if obj.sub_params is not None or "sub_params" in nullable:
            self.sub_params_json = dict_to_db_json(obj.sub_params)
        if obj.cluster_ad is not None or "cluster_ad" in nullable:
            self.cluster_ad_json = dict_to_db_json(obj.cluster_ad)
        if obj.first_proc is not None or "first_proc" in nullable:
            self.first_proc = obj.first_proc
        if obj.num_procs is not None or "num_procs" in nullable:
            self.num_procs = obj.num_procs
        if obj.status is not None or "status" in nullable:
            self.status_json = self._status_obj_to_json(obj.status)

    def update_from_db_dict(self, db_dict: dict):
        """Update the db row object from a dict"""
        if "task_id" in db_dict:
            self.task_id = db_dict["task_id"]
        if "sub_params_json" in db_dict:
            self.sub_params_json = db_dict["sub_params_json"]
        if "cluster_ad_json" in db_dict:
            self.cluster_ad_json = db_dict["cluster_ad_json"]
        if "first_proc" in db_dict:
            self.first_proc = db_dict["first_proc"]
        if "num_procs" in db_dict:
            self.num_procs = db_dict["num_procs"]
        if "status_json" in db_dict:
            self.status_json = db_dict["status_json"]

    def __get_attr__(self, _name: str) -> Any: ...


class HTCJobEvent(db.Model):
    """HTCJobEvent DB model"""

    __tablename__ = "htc_job_events"

    id = db.Column(db.String(64), primary_key=True)
    creation_date = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),  # pylint: disable=not-callable
    )
    cluster_id = db.Column(db.Integer, db.ForeignKey("htc_cluster.id"))
    proc_id = db.Column(db.Integer)
    timestamp = db.Column(db.Double)
    event_type = db.Column(db.Integer)
    details_json = db.Column(db.Text())

    # cluster = db.relationship("HTCCluster", back_populates="job_events")
    # cluster: Mapped[HTCCluster] = relationship(
    #     "HTCCluster", back_populates="job_events"
    # )

    def _dump_camelcase_dict(self) -> dict:
        if self.creation_date:  # type: ignore
            creation_date = str(self.creation_date)
        else:
            creation_date = None
        if self.details_json:  # type: ignore
            details = json.loads(self.details_json)  # type: ignore
        else:
            details = None
        return {
            "id": self.id,
            "creationDate": creation_date,
            "clusterId": self.cluster_id,
            "procId": self.proc_id,
            "timestamp": self.timestamp,
            "eventType": self.event_type,
            "details": details,
        }

    def dump_obj(self) -> models.HTCJobEvent:
        """Dumps the DB entity as an HTCJobEvent python object"""

        htc_job_event_schema = models.SchemaInstances.get_htc_job_event_schema()
        return htc_job_event_schema.load(self._dump_camelcase_dict())  # type: ignore

    @classmethod
    def obj_to_db_dict(
        cls, obj: models.HTCJobEvent, nullable: Optional[list] = None
    ) -> dict:
        """Dump an HTCJobEvent python object as DB-mappable dict."""

        d = dataclasses.asdict(obj)
        del_nulls_if_not_nullable(d, nullable)

        if "details" in d:
            del d["details"]
            d["details_json"] = dict_to_db_json(obj.details)
        return d
