from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def build_database_url(database_url: Optional[str] = None) -> str:
    configured_value = database_url or os.environ.get("TASK_SOLVER_DB_PATH")
    if configured_value and "://" in configured_value:
        return configured_value

    db_path = Path(configured_value) if configured_value else Path("data") / "task_solver.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path.resolve()}"


def create_session_factory(database_url: Optional[str] = None) -> Tuple[Engine, sessionmaker]:
    engine = create_engine(
        build_database_url(database_url),
        connect_args={"check_same_thread": False},
    )
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return engine, session_factory


def session_dependency(request: Request) -> Session:
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()
