"""API router"""


# pylint: disable=unnecessary-pass
# pylint: disable=unused-argument

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path

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


router = APIRouter()


@router.get(
    "/status",
    tags=["General"],
    responses={200: {"description": "Server status", "model": ServerStatus}},
    openapi_extra=REMOVE_OPERATION_ID_AND_SUMMARY,
)
async def get_server_status():
    "Server status"
    pass


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
    pass


@router.get(
    "/tasks-completed",
    tags=["Tasks"],
    responses={200: {"model": TaskListResponse}},
    openapi_extra=REMOVE_OPERATION_ID_AND_SUMMARY,
)
async def get_tasks_completed():
    "Tasks completed"
    pass


@router.get(
    "/tasks-queued",
    tags=["Tasks"],
    responses={200: {"model": TaskListResponse}},
    openapi_extra=REMOVE_OPERATION_ID_AND_SUMMARY,
)
async def get_tasks_queued():
    "Tasks queued"
    pass


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
    pass


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
    pass


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
    pass


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
