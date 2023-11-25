"""simple-task-api-htc.main"""

import asyncio
from contextlib import asynccontextmanager
import json
from typing import cast

from fastapi import FastAPI
from hypercorn.asyncio import serve
from hypercorn.config import Config
from hypercorn.typing import Framework

from .api import router as api_router
from .api.schemas import OPENAPI_TAGS
from .common import db_models
from .version import __version__


@asynccontextmanager
async def fastapi_lifespan(app: FastAPI):
    """app lifespan"""

    print(f"lifespan init {app}")
    # init db
    db_models.db.my_init()

    yield

    # close db
    print(f"lifespan close {app}")
    db_models.db.my_close()


def create_app() -> FastAPI:
    """FastAPI app factory"""

    app = FastAPI(
        title="TaskAPI for HTCondor",
        version=__version__,
        description=(
            "RESTful API for HTCondor HPC job scheduler (PydanticV2-based spec output)."
        ),
        openapi_tags=OPENAPI_TAGS,
        lifespan=fastapi_lifespan,
    )
    app.include_router(api_router, prefix="/api")
    return app


def get_config() -> Config:
    """get FastAPI config"""

    config = Config()
    config.bind = ["localhost:8080"]
    config.use_reloader = True
    return config


def cli() -> None:
    """routine called from cli (when installed as a package)"""

    app = create_app()
    with open("./generated-spec/openapi.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(app.openapi(), indent=2))
    shutdown_event = asyncio.Event()
    asyncio.run(
        serve(
            app=cast(Framework, app),
            config=get_config(),
            shutdown_trigger=shutdown_event.wait,
        )
    )
