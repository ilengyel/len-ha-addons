from __future__ import annotations

from typing import Dict, List, Optional, Set

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db import session_dependency
from app.models import Task, TaskRun, TaskRunItem, User
from app.utils import resolve_return_to
from app.web import templates


router = APIRouter()


@router.post("/users")
def create_user(
    name: str = Form(...),
    return_to: str = Form("/"),
    session: Session = Depends(session_dependency),
) -> RedirectResponse:
    trimmed = name.strip()
    if trimmed:
        existing = session.scalar(
            select(User).where(func.lower(User.name) == trimmed.lower())
        )
        if existing is None:
            session.add(User(name=trimmed))
            session.commit()
    return RedirectResponse(
        url=resolve_return_to(return_to, "/"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/users/{user_id}/edit")
def edit_user(
    user_id: int,
    name: str = Form(...),
    return_to: str = Form("/"),
    session: Session = Depends(session_dependency),
) -> RedirectResponse:
    user = session.get(User, user_id)
    if user is not None:
        trimmed = name.strip()
        if trimmed:
            user.name = trimmed
            session.commit()
    return RedirectResponse(
        url=resolve_return_to(return_to, "/"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


def load_task(session: Session, task_id: int) -> Optional[Task]:
    return session.scalar(
        select(Task)
        .options(selectinload(Task.checklist_items))
        .where(Task.id == task_id)
    )


def load_users(session: Session) -> List[User]:
    return list(session.scalars(select(User).order_by(User.name.asc())))


def render_completion_page(
    request: Request,
    task: Task,
    users: List[User],
    error: Optional[str] = None,
    selected_user_id: Optional[int] = None,
    new_user_name: str = "",
    checked_item_ids: Optional[Set[int]] = None,
    status_code: int = status.HTTP_200_OK,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "complete_task.html",
        {
            "task": task,
            "users": users,
            "error": error,
            "selected_user_id": selected_user_id,
            "new_user_name": new_user_name,
            "checked_item_ids": checked_item_ids or set(),
        },
        status_code=status_code,
    )


def resolve_user(session: Session, existing_user_id: Optional[int], new_user_name: str) -> Optional[User]:
    trimmed_name = new_user_name.strip()
    if trimmed_name:
        existing_match = session.scalar(
            select(User).where(func.lower(User.name) == trimmed_name.lower())
        )
        if existing_match is not None:
            return existing_match

        user = User(name=trimmed_name)
        session.add(user)
        session.flush()
        return user

    if existing_user_id is None:
        return None

    return session.get(User, existing_user_id)


@router.get("/tasks/{task_id}/complete", response_class=HTMLResponse)
def start_task_flow(
    task_id: int,
    request: Request,
    session: Session = Depends(session_dependency),
) -> HTMLResponse:
    task = load_task(session, task_id)
    if task is None:
        return templates.TemplateResponse(
            request,
            "missing.html",
            {"message": "Task not found."},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return render_completion_page(request, task, load_users(session))


@router.post("/tasks/{task_id}/complete", response_class=HTMLResponse)
def complete_task(
    task_id: int,
    request: Request,
    existing_user_id: str = Form(""),
    new_user_name: str = Form(""),
    completed_item_ids: Optional[List[int]] = Form(None),
    session: Session = Depends(session_dependency),
) -> HTMLResponse:
    task = load_task(session, task_id)
    if task is None:
        return templates.TemplateResponse(
            request,
            "missing.html",
            {"message": "Task not found."},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    selected_user_id = int(existing_user_id) if existing_user_id.strip().isdigit() else None
    checked_item_ids = set(completed_item_ids or [])
    all_item_ids = {item.id for item in task.checklist_items}
    users = load_users(session)

    if not task.checklist_items:
        return render_completion_page(
            request,
            task,
            users,
            error="Add at least one checklist item on the main board before completing this task.",
            selected_user_id=selected_user_id,
            new_user_name=new_user_name,
            checked_item_ids=checked_item_ids,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user = resolve_user(session, selected_user_id, new_user_name)
    if user is None:
        session.rollback()
        return render_completion_page(
            request,
            task,
            users,
            error="Select a person or type a new name before marking the task complete.",
            selected_user_id=selected_user_id,
            new_user_name=new_user_name,
            checked_item_ids=checked_item_ids,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if checked_item_ids != all_item_ids:
        session.rollback()
        return render_completion_page(
            request,
            task,
            users,
            error="Tick every checklist item before marking the task complete.",
            selected_user_id=user.id,
            new_user_name=new_user_name,
            checked_item_ids=checked_item_ids,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    task_run = TaskRun(
        task_id=task.id,
        user_id=user.id,
        task_title_snapshot=task.title,
        user_name_snapshot=user.name,
    )
    session.add(task_run)
    session.flush()

    for item in task.checklist_items:
        session.add(
            TaskRunItem(
                task_run_id=task_run.id,
                checklist_item_id=item.id,
                label=item.title,
                completed=True,
            )
        )

    session.commit()
    return RedirectResponse(url="/?completed=1", status_code=status.HTTP_303_SEE_OTHER)
