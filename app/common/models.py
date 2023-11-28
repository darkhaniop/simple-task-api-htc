"""Common models"""

# pylint: disable=too-few-public-methods

import json
import dataclasses
from datetime import datetime
from typing import Optional


from marshmallow import Schema, fields, validate, post_load


class Submission:
    """Submissions"""

    sub_id: Optional[str]
    exec_cmd: str
    args: list[str]
    envvars: dict[str, str]
    stream_type: str
    proc_method: str
    proc_inputs: list["Submission"]
    proc_params: dict
    raw_channel_name: str
    raw_channel_params: dict

    def __init__(
        self,
        exec_cmd: str,
        args: Optional[list[str]] = None,
        envvars: Optional[dict[str, str]] = None,
    ) -> None:
        self.sub_id = None
        self.exec_cmd = exec_cmd
        if args is not None:
            self.args = args.copy()
        else:
            self.args = []
        if envvars is not None:
            self.envvars = json.loads(json.dumps(envvars))
        else:
            self.envvars = {}


def camelcase(key: str) -> str:
    """Convert to camel case"""
    parts = iter(key.split("_"))
    return next(parts) + "".join(i.title() for i in parts)


class OrderedCamelCaseSchema(Schema):
    """Schema that uses camel-case for its external representation
    and snake-case for its internal representation.
    """

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        """Enable key ordering in the parent schema"""

        ordered = True


class ConstField(fields.String):
    """Generic class for const fields."""

    _const_value: str

    def __init__(self, const_value: str, **kwargs) -> None:
        self._const_value = const_value
        kwargs["dump_default"] = self._const_value
        kwargs["validate"] = validate.OneOf([self._const_value])
        super().__init__(**kwargs)


class TaskStates:
    """Task states."""

    QUEUED = 0
    SUBMITTED = 1
    COMPLETED = 2
    COMPLETED_WITH_ERROR = 3
    TIMED_OUT = 4
    IGNORED = -1


class SubmissionSchema(OrderedCamelCaseSchema):
    """Submission schema definition."""

    stream_type = fields.String(required=True, validate=validate.OneOf(["raw", "proc"]))
    args = fields.List(fields.String())

    @post_load
    def make_submission(self, data, **_kwargs) -> Submission:
        """Convert dict to a submission object"""

        submission = Submission(data["exec_cmd"], data["args"])
        if "sub_id" in data:
            submission.sub_id = data["sub_id"]
        return submission


class JobEventSchema(OrderedCamelCaseSchema):
    """JobEvent schema definition"""

    cluster_id = fields.Integer(required=True)
    proc_id = fields.Integer(required=True)
    timestamp = fields.Float(required=True)
    event_type = fields.String()
    details = fields.Dict()


@dataclasses.dataclass
class ServerStatus:
    """Server status"""

    response_date: datetime
    n_tasks_queued: int
    n_tasks_submitted: int
    n_tasks_completed: int
    n_tasks_completed_with_error: int
    n_tasks_timed_out: int


class ServerStatusSchema(OrderedCamelCaseSchema):
    """ServerStatus schema definition"""

    kind = ConstField("dtaskapi-htc-server-status")
    response_date = fields.DateTime()
    n_tasks_queued = fields.Integer()
    n_tasks_submitted = fields.Integer()
    n_tasks_completed = fields.Integer()
    n_tasks_completed_with_error = fields.Integer()
    n_tasks_timed_out = fields.Integer()


@dataclasses.dataclass
class Task:
    """Task python object"""

    id: Optional[str] = None
    creation_date: Optional[datetime] = None
    sub_params: Optional[dict] = None
    state: int = -1
    state_date: Optional[datetime] = None
    retries_left: int = 0
    cluster_id: Optional[int] = None
    proc_id: Optional[int] = None
    expiration_date: Optional[datetime] = None


class TaskSchema(OrderedCamelCaseSchema):
    """Task schema definition"""

    id = fields.String(required=True)
    creation_date = fields.DateTime()
    sub_params = fields.Dict(fields.String(), fields.String(), allow_none=True)
    state = fields.Integer()
    state_date = fields.DateTime()
    retries_left = fields.Integer(load_default=3)
    cluster_id = fields.Integer(allow_none=True)
    proc_id = fields.Integer(allow_none=True)
    expiration_date = fields.DateTime(allow_none=True)
    latest_sub_id = fields.String()

    @post_load
    def convert_sub_params(self, data, **_kwargs):
        """Convert submission params."""
        if "sub_params" in data and isinstance(data["sub_params"], str):
            data["sub_params"] = json.loads(data["sub_params"])
        return Task(**data)


class TaskCreateSchema(OrderedCamelCaseSchema):
    """TaskCreate schema definition"""

    id = fields.String()
    state = fields.Integer(load_default=TaskStates.QUEUED)
    sub_params = fields.Dict(fields.String(), fields.String())
    retries_left = fields.Integer(load_default=2)

    @post_load
    def make_dataclass_object(self, data, **_kwargs):
        """Convert dict to a Task python object"""
        return Task(**data)


@dataclasses.dataclass
class TaskUpdateRequest:
    """Task update request"""

    state: int = -1
    state_date: Optional[datetime] = None
    retries_left: int = 0
    cluster_id: Optional[int] = None
    proc_id: Optional[int] = None
    expiration_date: Optional[datetime] = None
    reset_cluster_id: bool = False
    reset_proc_id: bool = False
    reset_expiration_date: bool = False


class TaskUpdateRequestSchema(OrderedCamelCaseSchema):
    """TaskUpdateRequest schema definition"""

    state = fields.Integer()
    retries_left = fields.Integer()
    cluster_id = fields.Integer(allow_none=True)
    proc_id = fields.Integer(allow_none=True)
    expiration_date = fields.DateTime(allow_none=True)

    @post_load
    def make_dataclass_object(self, data, **_kwargs):
        """Create TaskUpdateRequest from a dict"""
        if "cluster_id" in data and data["cluster_id"] is None:
            data["reset_cluster_id"] = True
        if "proc_id" in data and data["proc_id"] is None:
            data["reset_proc_id"] = True
        if "expiration_date" in data and data["expiration_date"] is None:
            data["reset_expiration_date"] = True
        return TaskUpdateRequest(**data)


@dataclasses.dataclass
class TaskListResponse:
    """TaskListResponse"""

    response_date: datetime
    items: list[Task]


class TaskListResponseSchema(OrderedCamelCaseSchema):
    """TaskListResponse schema definition"""

    kind = ConstField("hpctask-list")
    response_date = fields.DateTime()
    items = fields.List(fields.Nested(TaskSchema), required=True)

    @post_load
    def make_dataclass_object(self, data, **_kwargs):
        """Create TaskListResponse from a dict"""
        return TaskListResponse(**data)


class HTCClusterStates:
    """HTCClusterStates"""

    CREATED = 0
    EXECUTING = 1
    COMPLETED_OK = 2
    COMPLETED_ERROR = 3


@dataclasses.dataclass
class HTCClusterStatus:
    """HTCClusterStatus"""

    cluster_state: Optional[int] = None
    procs: Optional[list[dict]] = None


class HTCClusterStatusPartial(OrderedCamelCaseSchema):
    """HTCClusterStatuc partial schema"""

    cluster_state = fields.Integer()
    procs = fields.List(fields.Dict())

    @post_load
    def make_dataclass_object(self, data, **_kwargs):
        """Create HTCClusterStatus from a dict"""
        return HTCClusterStatus(**data)


@dataclasses.dataclass
class HTCCluster:
    """HTCCluster"""

    id: Optional[int] = None
    creation_date: Optional[datetime] = None
    task_id: Optional[str] = None
    sub_params: Optional[dict] = None
    cluster_ad: Optional[dict] = None
    first_proc: Optional[int] = None
    num_procs: Optional[int] = None
    status: Optional[HTCClusterStatus] = None

    def __post_init__(self):
        if isinstance(self.status, dict):
            self.status = HTCClusterStatusPartial().load(self.status)


class HTCClusterSchema(OrderedCamelCaseSchema):
    """HTCCluster schema definition"""

    id = fields.Integer(required=True)
    creation_date = fields.DateTime()
    task_id = fields.String()
    sub_params = fields.Dict()
    cluster_ad = fields.Dict()
    first_proc = fields.Integer()
    num_procs = fields.Integer()
    status = fields.Nested(HTCClusterStatusPartial)

    @post_load
    def make_dataclass_object(self, data, **_kwargs):
        """Create HTCCluster object from a dict"""
        return HTCCluster(**data)


class HTCClusterCreateSchema(OrderedCamelCaseSchema):
    """HTCClusterCreate schema definition"""

    id = fields.Integer(required=True)
    task_id = fields.String(load_default="-")
    sub_params = fields.Dict()
    cluster_ad = fields.Dict()
    first_proc = fields.Integer(load_default=0)
    num_procs = fields.Integer()
    status = fields.Nested(HTCClusterStatusPartial)

    @post_load
    def make_dataclass_object(self, data, **_kwargs):
        """Create HTCCluster from a dict"""
        return HTCCluster(**data)


@dataclasses.dataclass
class HTCClusterWithTask:
    """HTCClusterWithTask"""

    cluster: HTCCluster
    task: Task
    extra: dict


class HTCClusterWithTaskSchema(OrderedCamelCaseSchema):
    """HTCClusterWithTask schema definition"""

    kind = ConstField("htc-cluster-with-task")
    cluster = fields.Nested(HTCClusterSchema)
    task = fields.Nested(TaskSchema)
    extra = fields.Dict()


@dataclasses.dataclass
class HTCJobEvent:
    """HTCJobEvent"""

    cluster_id: int
    proc_id: int
    timestamp: float
    event_type: str
    details: dict

    id: Optional[str] = None
    creation_date: Optional[datetime] = None

    def gen_entry_id(self) -> str:
        """Generate JobEvent entry ID"""
        self.id = f"{self.cluster_id}-{self.proc_id}-{self.timestamp}-{self.event_type}"
        return self.id


class HTCJobEventSchema(OrderedCamelCaseSchema):
    """HTCJobEvent schema definition"""

    id = fields.String()
    creation_date = fields.DateTime()
    cluster_id = fields.Integer(required=True)
    proc_id = fields.Integer(required=True)
    timestamp = fields.Float(required=True)
    event_type = fields.String(required=True)
    details = fields.Dict()

    @post_load
    def make_dataclass_object(self, data, **_kwargs) -> HTCJobEvent:
        """Create HTCJobEvent object from a dict"""
        print(f"in make_dataclass_obj:\n{data}")
        return HTCJobEvent(**data)


class HTCJobEventPostSchema(OrderedCamelCaseSchema):
    """HTCJobEventPost (create) schema definition"""

    cluster_id = fields.Integer()
    proc_id = fields.Integer()
    timestamp = fields.Float()
    event_type = fields.String()
    details = fields.Dict()

    @post_load
    def make_dataclass_object(self, data, **_kwargs) -> HTCJobEvent:
        """Create HTCJobEvent object from a dict"""
        return HTCJobEvent(**data)


@dataclasses.dataclass
class LogEntryCreate:
    """LogEntryCreate"""

    cluster_id: int
    proc_id: int
    timestamp: float
    event_type: str
    details: dict

    def get_entry_id(self) -> str:
        """Get the LogEntry id based on its properties"""
        return f"{self.cluster_id}-{self.proc_id}-{self.timestamp}-{self.event_type}"


class LogEntryCreateSchema(OrderedCamelCaseSchema):
    """LogEntryCreate schema definition"""

    kind = ConstField("log-entry-new")
    cluster_id = fields.Integer(required=True)
    proc_id = fields.Integer(required=True)
    timestamp = fields.Float(required=True)
    event_type = fields.String()
    details = fields.Dict()

    @post_load
    def make_dataclass_object(self, data, **_kwargs):
        """Create LogEntryCreate object from a dict"""
        return LogEntryCreate(**data)


class SchemaInstances:
    """SchemaInstances, holds singleton schema instances"""

    _task_schema: Optional[TaskSchema] = None
    _task_create_schema: Optional[TaskCreateSchema] = None
    _task_update_request_schema: Optional[TaskUpdateRequestSchema] = None
    _task_list_response_schema: Optional[TaskListResponseSchema] = None
    _htc_cluster_schema: Optional[HTCClusterSchema] = None
    _htc_cluster_create_schema: Optional[HTCClusterCreateSchema] = None
    _htc_cluster_with_task_schema: Optional[HTCClusterWithTaskSchema] = None
    _htc_job_event_schema: Optional[HTCJobEventSchema] = None
    _htc_job_event_create_schema: Optional[HTCJobEventSchema] = None

    @classmethod
    def get_task_schema(cls) -> TaskSchema:
        """Get the TaskSchema instance"""
        if not cls._task_schema:
            cls._task_schema = TaskSchema()
        return cls._task_schema

    @classmethod
    def get_task_create_schema(cls) -> TaskCreateSchema:
        """Get the TaskCreateSchema instance"""
        if not cls._task_create_schema:
            cls._task_create_schema = TaskCreateSchema()
        return cls._task_create_schema

    @classmethod
    def get_task_update_request_schema(cls) -> TaskUpdateRequestSchema:
        """Get the TaskUpdateRequestSchema instance"""
        if not cls._task_update_request_schema:
            cls._task_update_request_schema = TaskUpdateRequestSchema()
        return cls._task_update_request_schema

    @classmethod
    def get_task_list_response_schema(cls) -> TaskListResponseSchema:
        """Get the TaskListResponseSchema instance"""
        if not cls._task_list_response_schema:
            cls._task_list_response_schema = TaskListResponseSchema()
        return cls._task_list_response_schema

    @classmethod
    def get_htc_cluster_schema(cls) -> HTCClusterSchema:
        """Get the HTCClusterSchema instance"""
        if not cls._htc_cluster_schema:
            cls._htc_cluster_schema = HTCClusterSchema()
        return cls._htc_cluster_schema

    @classmethod
    def get_htc_cluster_create_schema(cls) -> HTCClusterCreateSchema:
        """Get the HTCClusterSchema instance"""
        if not cls._htc_cluster_create_schema:
            cls._htc_cluster_create_schema = HTCClusterCreateSchema()
        return cls._htc_cluster_create_schema

    @classmethod
    def get_htc_cluster_with_task_schema(cls) -> HTCClusterWithTaskSchema:
        """Get the HTCClusterSchema instance"""
        if not cls._htc_cluster_with_task_schema:
            cls._htc_cluster_with_task_schema = HTCClusterWithTaskSchema()
        return cls._htc_cluster_with_task_schema

    @classmethod
    def get_htc_job_event_schema(cls) -> HTCJobEventSchema:
        """Get the HTCJobEventSchema instance"""
        if not cls._htc_job_event_schema:
            cls._htc_job_event_schema = HTCJobEventSchema()
        return cls._htc_job_event_schema

    @classmethod
    def get_htc_job_event_create_schema(cls) -> HTCJobEventSchema:
        """Get the HTCJobEventCreateSchema instance"""
        if not cls._htc_job_event_create_schema:
            cls._htc_job_event_create_schema = HTCJobEventSchema(
                exclude=["id", "creation_date"]
            )
        return cls._htc_job_event_create_schema
