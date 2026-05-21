from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.db import session_dependency


def get_session(request: Request) -> Session:
    dependency = session_dependency(request)
    return next(dependency)
