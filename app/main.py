"""simple-task-api-htc.main"""

from fastapi import FastAPI

from .version import __version__


def create_app() -> FastAPI:
    """FastAPI app factory"""

    app = FastAPI(
        title="TaskAPI for HTCondor",
        version=__version__,
        description=("RESTful API for HTCondor HPC job scheduler (FastAPI-based)."),
    )
    return app
