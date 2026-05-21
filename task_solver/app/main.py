from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import create_session_factory
from app.models import Base
from app.routers import reports, runs, tasks
from app.seed import seed_default_data
from app.web import STATIC_DIR


def create_app(database_url: Optional[str] = None, seed_defaults: bool = True) -> FastAPI:
    engine, session_factory = create_session_factory(database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.engine = engine
        app.state.session_factory = session_factory
        Base.metadata.create_all(bind=engine)
        if seed_defaults:
            with session_factory() as session:
                seed_default_data(session)
        yield
        engine.dispose()

    app = FastAPI(title="Task Solver", lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    app.include_router(tasks.router)
    app.include_router(runs.router)
    app.include_router(reports.router)
    return app


app = create_app()
