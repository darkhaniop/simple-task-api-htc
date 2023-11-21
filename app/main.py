"""simple-task-api-htc.main"""

from fastapi import FastAPI

from .api import router as api_router
from .api.schemas import OPENAPI_TAGS
from .version import __version__


def create_app() -> FastAPI:
    """FastAPI app factory"""

    app = FastAPI(
        title="TaskAPI for HTCondor",
        version=__version__,
        description=(
            "RESTful API for HTCondor HPC job scheduler (PydanticV2-based spec output)."
        ),
        openapi_tags=OPENAPI_TAGS,
    )
    app.include_router(api_router, prefix="/api")
    return app
