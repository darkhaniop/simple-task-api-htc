"""API router"""


# pylint: disable=unnecessary-pass
# pylint: disable=unused-argument

from __future__ import annotations

from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from .schemas import (
    Task,
    TaskCreate,
    TaskListResponse,
    TaskUpdateRequest,
    ServerStatus,
    HTCJobEvent,
    HTCJobEventPost,
    LogEntryCreate,
    HTCCluster,
    HTCClusterCreate,
    HTCClusterWithTask,
    REMOVE_OPERATION_ID_AND_SUMMARY,
)
from ..common import db_ops
from ..common import models as msm_models
from ..common.models import SchemaInstances


router = APIRouter()


@router.get(
    "/status",
    tags=["General"],
    responses={200: {"description": "Server status", "model": ServerStatus}},
    openapi_extra=REMOVE_OPERATION_ID_AND_SUMMARY,
)
async def get_server_status():
    "Server status"

    return asdict(db_ops.get_status())


@router.post(
    "/htc-clusters",
    tags=["HTCondor"],
    response_model=HTCCluster,
    openapi_extra=REMOVE_OPERATION_ID_AND_SUMMARY,
)
async def htc_cluster_collection_post(new_htc_cluster: HTCClusterCreate):
    """New HTC Cluster"""
    pass


@router.get(
    "/htc-clusters/{cluster_id}",
    tags=["HTCondor"],
    response_model=HTCClusterWithTask,
    openapi_extra=REMOVE_OPERATION_ID_AND_SUMMARY,
)
async def get_htc_cluster(
    cluster_id: Annotated[int, Path(description="The identifier of the cluster.")],
):
    """Show HTC Cluster"""
    pass


@router.get(
    "/tasks",
    tags=["Tasks"],
    response_model=TaskListResponse,
    openapi_extra=REMOVE_OPERATION_ID_AND_SUMMARY,
)
async def task_collection():
    "Tasks (all)"

    task_list_response = db_ops.get_tasks_all()
    response_schema = SchemaInstances.get_task_list_response_schema()
    print(task_list_response)
    return response_schema.dump(task_list_response)


@router.get(
    "/tasks-completed",
    tags=["Tasks"],
    responses={200: {"model": TaskListResponse}},
    openapi_extra=REMOVE_OPERATION_ID_AND_SUMMARY,
)
async def get_tasks_completed():
    "Tasks completed"

    task_list_response = db_ops.get_tasks_completed()
    response_schema = SchemaInstances.get_task_list_response_schema()
    print(task_list_response)
    return response_schema.dump(task_list_response)


@router.get(
    "/tasks-queued",
    tags=["Tasks"],
    responses={200: {"model": TaskListResponse}},
    openapi_extra=REMOVE_OPERATION_ID_AND_SUMMARY,
)
async def get_tasks_queued():
    "Tasks queued"

    task_list_response = db_ops.get_tasks_queued()
    response_schema = SchemaInstances.get_task_list_response_schema()
    print(task_list_response)
    return response_schema.dump(task_list_response)


@router.post(
    "/tasks",
    operation_id=None,
    summary=None,
    tags=["Tasks"],
    responses={200: {"description": "Created Task", "model": Task}},
    openapi_extra=REMOVE_OPERATION_ID_AND_SUMMARY,
)
async def task_collection_post(new_task: TaskCreate):
    "Create Task"

    task_create_schema = SchemaInstances.get_task_create_schema()
    new_task_msm: msm_models.Task = task_create_schema.loads(new_task.model_dump_json()) # type: ignore

    task = db_ops.create_task(new_task_msm)

    task_schema = SchemaInstances.get_task_schema()

    return task_schema.dump(task)


@router.get(
    "/tasks/{task_id}",
    tags=["Tasks"],
    response_model=Task,
    openapi_extra=REMOVE_OPERATION_ID_AND_SUMMARY,
)
async def get_task(
    task_id: Annotated[str, Path(description="The identifier of the Task.")],
):
    "Show Task"

    print(f"get task {task_id}")
    task = db_ops.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="not-found")

    task_schema = SchemaInstances.get_task_schema()

    return task_schema.dump(task)


@router.post(
    "/tasks/{task_id}",
    tags=["Tasks"],
    responses={200: {"description": "Updated Task", "model": Task}},
    openapi_extra=REMOVE_OPERATION_ID_AND_SUMMARY,
)
async def update_task(
    task_id: Annotated[str, Path(description="The identifier of the task.")],
    task_update: TaskUpdateRequest,
):
    "Update Task"

    task_update_request_schema = SchemaInstances.get_task_update_request_schema()
    task_update_request: msm_models.TaskUpdateRequest = task_update_request_schema.loads(task_update.model_dump_json()) # type: ignore
    task = db_ops.update_task(task_id, task_update_request)

    task_schema = SchemaInstances.get_task_schema()

    return task_schema.dump(task)


@router.post(
    "/htc-job-events",
    tags=["HTCondor"],
    response_model=HTCJobEvent,
    openapi_extra=REMOVE_OPERATION_ID_AND_SUMMARY,
)
async def htc_job_events_post(log_entry: HTCJobEventPost):
    """Post a new log entry"""
    pass


@router.get(
    "/log/{entry_id}", tags=["HTCondor"], openapi_extra=REMOVE_OPERATION_ID_AND_SUMMARY
)
async def log_entry_get(entry_id: int):
    """Get log entry"""
    pass


@router.post(
    "/log",
    tags=["HTCondor"],
    openapi_extra=REMOVE_OPERATION_ID_AND_SUMMARY,
)
async def log_entry_post(log_entry: LogEntryCreate):
    "Post a new log entry"
    pass
