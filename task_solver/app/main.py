from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from app.db import create_session_factory
from app.models import Base
from app.routers import debug, reports, runs, tasks
from app.seed import seed_default_data
from app.web import STATIC_DIR, build_debug_upload_dir

logger = logging.getLogger("uvicorn.error")


class IngressASGIMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            # Do not set root_path for static file routes to avoid Starlette StaticFiles bugs
            if not path.startswith("/static") and not path.startswith("/debug-media"):
                ingress_path = ""
                for name, value in scope.get("headers", []):
                    if name == b"x-ingress-path":
                        ingress_path = value.decode("utf-8").rstrip("/")
                        break
                if ingress_path:
                    scope = dict(scope)
                    scope["root_path"] = ingress_path

        await self.app(scope, receive, send)


def create_app(database_url: Optional[str] = None, seed_defaults: bool = True) -> FastAPI:
    engine, session_factory = create_session_factory(database_url)
    debug_upload_dir = build_debug_upload_dir(database_url)

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
    app.state.debug_upload_dir = debug_upload_dir
    app.add_middleware(IngressASGIMiddleware)

    @app.middleware("http")
    async def ingress_middleware(request: Request, call_next):
        ingress_path = request.headers.get("X-Ingress-Path")
        client_ip = request.client.host if request.client else "unknown"
        mode_str = f"Ingress ({ingress_path})" if ingress_path else "Direct"

        response = await call_next(request)

        if ingress_path and "location" in response.headers:
            ingress_path_clean = ingress_path.rstrip("/")
            location = response.headers["location"]
            if location.startswith("/") and not location.startswith(ingress_path_clean):
                response.headers["location"] = f"{ingress_path_clean}{location}"

        logger.info(f"[{mode_str}] {client_ip} - \"{request.method} {request.url.path}\" -> {response.status_code}")
        return response

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.mount("/debug-media", StaticFiles(directory=str(debug_upload_dir)), name="debug-media")

    app.include_router(tasks.router)
    app.include_router(runs.router)
    app.include_router(reports.router)
    app.include_router(debug.router)
    return app


app = create_app()
