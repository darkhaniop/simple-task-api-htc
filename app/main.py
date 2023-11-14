"""simple-task-api-htc.main"""

from fastapi import FastAPI


def create_app() -> FastAPI:
    """FastAPI app factory"""

    app = FastAPI(
        title="TaskAPI for HTCondor",
        version="0.0.2",
        description=("RESTful API for HTCondor HPC job scheduler (FastAPI-based)."),
    )
    return app
