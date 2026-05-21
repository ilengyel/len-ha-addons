from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import session_dependency
from app.models import ChecklistItem, Task, TaskRun
from app.utils import resolve_return_to
from app.web import templates


router = APIRouter()


def load_tasks(session: Session):
    result = session.scalars(
        select(Task)
        .options(selectinload(Task.checklist_items))
        .order_by(Task.created_at.desc(), Task.id.desc())
    )
    return list(result)


def load_recent_runs(session: Session):
    result = session.scalars(
        select(TaskRun).order_by(TaskRun.completed_at.desc(), TaskRun.id.desc()).limit(10)
    )
    return list(result)


def render_index(
    request: Request,
    session: Session,
    error: Optional[str] = None,
    status_code: int = status.HTTP_200_OK,
) -> HTMLResponse:
    message = None
    error = error or None
    if request.query_params.get("created") == "1":
        message = "Task added. Tap it to add checklist items and record a completion."
    elif request.query_params.get("completed") == "1":
        message = "Completion recorded."
    elif request.query_params.get("renamed") == "1":
        message = "Task renamed."
    elif request.query_params.get("deleted") == "1":
        message = "Task removed."
    elif request.query_params.get("updated") == "1":
        message = "Checklist updated."
    elif request.query_params.get("error") == "title":
        error = "Task title is required."

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "tasks": load_tasks(session),
            "recent_runs": load_recent_runs(session),
            "error": error,
            "message": message,
        },
        status_code=status_code,
    )


@router.get("/", response_class=HTMLResponse)
def index(request: Request, session: Session = Depends(session_dependency)) -> HTMLResponse:
    return render_index(request, session)


@router.post("/tasks")
def create_task(
    title: str = Form(...),
    domain: str = Form("Household"),
    session: Session = Depends(session_dependency),
) -> RedirectResponse:
    trimmed_title = title.strip()
    if not trimmed_title:
        return RedirectResponse(url="/?error=title#add-task", status_code=status.HTTP_303_SEE_OTHER)

    task = Task(title=trimmed_title, domain=domain or "Household")
    session.add(task)
    session.commit()
    return RedirectResponse(url=f"/?created=1#task-{task.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/tasks/{task_id}/edit")
def edit_task(
    task_id: int,
    title: str = Form(...),
    return_to: str = Form("/"),
    session: Session = Depends(session_dependency),
) -> RedirectResponse:
    task = session.get(Task, task_id)
    if task is None:
        return RedirectResponse(
            url=resolve_return_to(return_to, "/"),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    trimmed_title = title.strip()
    if trimmed_title:
        task.title = trimmed_title
        session.commit()

    default_url = f"/?renamed=1#task-{task_id}"
    return RedirectResponse(
        url=resolve_return_to(return_to, default_url),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/tasks/{task_id}/delete")
def delete_task(
    task_id: int,
    return_to: str = Form("/"),
    session: Session = Depends(session_dependency),
) -> RedirectResponse:
    task = session.get(Task, task_id)
    if task is not None:
        session.delete(task)
        session.commit()

    return RedirectResponse(
        url=resolve_return_to(return_to, "/?deleted=1"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/tasks/{task_id}/checklist")
def add_checklist_item(
    task_id: int,
    title: str = Form(...),
    return_to: str = Form("/"),
    session: Session = Depends(session_dependency),
) -> RedirectResponse:
    task = session.get(Task, task_id)
    if task is None:
        return RedirectResponse(
            url=resolve_return_to(return_to, "/"),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    trimmed_title = title.strip()
    if trimmed_title:
        next_order = len(task.checklist_items) + 1
        session.add(ChecklistItem(task_id=task.id, title=trimmed_title, sort_order=next_order))
        session.commit()

    default_url = f"/?updated=1#task-{task_id}"
    return RedirectResponse(
        url=resolve_return_to(return_to, default_url),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/tasks/{task_id}/checklist/{item_id}/edit")
def edit_checklist_item(
    task_id: int,
    item_id: int,
    title: str = Form(...),
    return_to: str = Form("/"),
    session: Session = Depends(session_dependency),
) -> RedirectResponse:
    item = session.get(ChecklistItem, item_id)
    if item is None or item.task_id != task_id:
        return RedirectResponse(
            url=resolve_return_to(return_to, "/"),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    trimmed_title = title.strip()
    if trimmed_title:
        item.title = trimmed_title
        session.commit()

    default_url = f"/?updated=1#task-{task_id}"
    return RedirectResponse(
        url=resolve_return_to(return_to, default_url),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/tasks/{task_id}/checklist/{item_id}/delete")
def delete_checklist_item(
    task_id: int,
    item_id: int,
    return_to: str = Form("/"),
    session: Session = Depends(session_dependency),
) -> RedirectResponse:
    item = session.get(ChecklistItem, item_id)
    if item is not None and item.task_id == task_id:
        session.delete(item)
        session.flush()
        remaining_items = list(
            session.scalars(
                select(ChecklistItem)
                .where(ChecklistItem.task_id == task_id)
                .order_by(ChecklistItem.sort_order.asc(), ChecklistItem.id.asc())
            )
        )
        for index, remaining_item in enumerate(remaining_items, start=1):
            remaining_item.sort_order = index
        session.commit()

    default_url = f"/?updated=1#task-{task_id}"
    return RedirectResponse(
        url=resolve_return_to(return_to, default_url),
        status_code=status.HTTP_303_SEE_OTHER,
    )
