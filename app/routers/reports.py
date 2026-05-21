from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import session_dependency
from app.models import TaskRun
from app.web import templates


router = APIRouter()


@router.get("/reports", response_class=HTMLResponse)
def reports(request: Request, session: Session = Depends(session_dependency)) -> HTMLResponse:
    recent_runs = list(
        session.scalars(select(TaskRun).order_by(TaskRun.completed_at.desc(), TaskRun.id.desc()).limit(20))
    )
    user_summary = list(
        session.execute(
            select(TaskRun.user_name_snapshot, func.count(TaskRun.id).label("total"))
            .group_by(TaskRun.user_name_snapshot)
            .order_by(func.count(TaskRun.id).desc(), TaskRun.user_name_snapshot.asc())
        )
    )
    task_summary = list(
        session.execute(
            select(TaskRun.task_title_snapshot, func.count(TaskRun.id).label("total"))
            .group_by(TaskRun.task_title_snapshot)
            .order_by(func.count(TaskRun.id).desc(), TaskRun.task_title_snapshot.asc())
        )
    )

    message = None
    if request.query_params.get("created") == "1":
        message = "Completion recorded in the backend. Reports now include the new task run."

    return templates.TemplateResponse(
        request,
        "reports.html",
        {
            "recent_runs": recent_runs,
            "user_summary": user_summary,
            "task_summary": task_summary,
            "message": message,
        },
    )
