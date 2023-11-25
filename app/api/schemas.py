"""Simple TaskAPI HTC Models"""


# pylint: disable=missing-class-docstring

from datetime import datetime
from typing import Any, Dict, List, Annotated, Literal

from pydantic import BaseModel, Field


OPENAPI_TAGS = [
    {
        "name": "Tasks",
        "description": "Task is a higher level abstraction for managing HTCondor submissions.",
    },
    {"name": "Log Entries", "description": "Management of task execution logs."},
    {"name": "HTCondor", "description": "Management of HTCondor clusters."},
]


def delete_title(schema):
    """Deletes title from schema properties"""
    schema.pop("summary", None)  # remove summary of model
    schema.pop("title", None)  # remove title of model
    schema.pop("operationId", None)  # remove operationId of model
    for _field_name, field_props in schema.get("properties", {}).items():
        field_props.pop("title", None)  # remove title of fields


REMOVE_OPERATION_ID_AND_SUMMARY = {
    "operationId": None,
    "summary": None,
    "responses": {422: None},
}


class HTCClusterStatusPartial(BaseModel):
    clusterState: int
    procs: List[Dict[str, Any]]

    @staticmethod
    def _schema_extra(schema):
        """json_schema_extra for HTCClusterStatusPartial"""

        delete_title(schema)
        schema.pop("required", None)

    model_config = {"json_schema_extra": _schema_extra}


class HTCClusterCreate(BaseModel):
    id: int
    taskId: str = "-"
    subParams: Dict[str, Any]
    clusterAd: Dict[str, Any]
    firstProc: int = 0
    numProcs: int
    status: HTCClusterStatusPartial

    @staticmethod
    def _schema_extra(schema):
        """json_schema_extra for HTCClusterCreate"""

        delete_title(schema)
        schema["required"] = ["id"]

    model_config = {"json_schema_extra": _schema_extra}


class HTCCluster(BaseModel):
    id: int
    creationDate: datetime
    taskId: str
    subParams: Dict[str, Any]
    clusterAd: Dict[str, Any]
    firstProc: int
    numProcs: int
    status: HTCClusterStatusPartial

    @staticmethod
    def _schema_extra(schema):
        """json_schema_extra for HTCCluster"""

        delete_title(schema)
        schema["required"] = ["id"]

    model_config = {"json_schema_extra": _schema_extra}


class HTCClusterWithTask(BaseModel):
    kind: Annotated[
        Literal["htc-cluster-with-task"],
        Field(default_factory=lambda: "htc-cluster-with-task"),
    ]
    cluster: HTCCluster
    task: "Task"
    extra: Dict[str, Any]

    @staticmethod
    def _schema_extra(schema):
        """json_schema_extra for HTCClusterWithTask"""

        delete_title(schema)
        schema.pop("required", None)

    model_config = {"json_schema_extra": _schema_extra}


class HTCJobEvent(BaseModel):
    id: str
    creationDate: datetime
    clusterId: int
    procId: int
    timestamp: float
    eventType: str
    details: Annotated[Dict[str, Any], Field(...)]

    @staticmethod
    def _schema_extra(schema):
        """json_schema_extra for HTCJobEvent"""

        delete_title(schema)
        schema["required"] = ["clusterId", "procId", "eventType", "timestamp"]

    model_config = {"json_schema_extra": _schema_extra}


class HTCJobEventPost(BaseModel):
    clusterId: int
    procId: int
    timestamp: float
    eventType: str
    details: Dict[str, Any]

    @staticmethod
    def _schema_extra(schema):
        """json_schema_extra for HTCJobEventPost"""

        delete_title(schema)
        schema.pop("required", None)

    model_config = {"json_schema_extra": _schema_extra}


class LogEntryCreate(BaseModel):
    kind: Annotated[
        Literal["log-entry-new"], Field(default_factory=lambda: "log-entry-new")
    ]
    clusterId: int
    procId: int
    timestamp: float
    eventType: str
    details: Dict[str, Any]

    @staticmethod
    def _schema_extra(schema):
        """json_schema_extra for LogEntryCreate"""

        delete_title(schema)
        schema["required"] = ["clusterId", "procId", "timestamp"]

    model_config = {"json_schema_extra": _schema_extra}


class ServerStatus(BaseModel):
    kind: Annotated[
        Literal["dtaskapi-htc-server-status"],
        Field(default_factory=lambda: "dtaskapi-htc-server-status"),
    ]
    responseDate: Annotated[datetime, Field()]
    nTasksQueued: Annotated[int, Field()]
    nTasksSubmitted: Annotated[int, Field()]
    nTasksCompleted: Annotated[int, Field()]
    nTasksCompletedWithError: int
    nTasksTimedOut: int

    @staticmethod
    def _schema_extra(schema):
        """json_schema_extra for ServerStatus"""

        delete_title(schema)
        schema.pop("required", None)

    model_config = {"json_schema_extra": _schema_extra}


class TaskCreate(BaseModel):
    id: str = Field(default_factory=lambda: "")
    state: int = 0
    subParams: Dict[str, str] = Field(default_factory=lambda: {})
    retriesLeft: int = 2

    model_config = {"json_schema_extra": delete_title}


class Task(BaseModel):
    id: str
    creationDate: datetime
    subParams: Dict[str, str]
    state: int
    stateDate: datetime
    retriesLeft: int = 3
    clusterId: int | None = None
    procId: int | None = None
    expirationDate: datetime | None = None
    latestSubId: str | None = None

    @staticmethod
    def _schema_extra(schema):
        """json_schema_extra for Task"""

        delete_title(schema)
        schema["required"] = ["id"]

    model_config = {"json_schema_extra": _schema_extra}


class TaskUpdateRequest(BaseModel):
    state: int
    retriesLeft: int
    clusterId: int
    procId: int
    expirationDate: datetime

    @staticmethod
    def _schema_extra(schema):
        """json_schema_extra for TaskUpdateRequest"""

        delete_title(schema)
        schema.pop("required", None)

    model_config = {"json_schema_extra": _schema_extra}


class TaskListResponse(BaseModel):
    kind: Annotated[
        Literal["hpctask-list"], Field(default_factory=lambda: "hpctask-list")
    ]
    responseDate: datetime
    items: list[Task]

    model_config = {"json_schema_extra": delete_title}
