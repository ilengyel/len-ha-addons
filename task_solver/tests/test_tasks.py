from sqlalchemy import select

from app.models import ChecklistItem, Task, TaskRun, TaskRunItem, User


def test_create_task_and_manage_checklist(client) -> None:
    create_response = client.post(
        "/tasks",
        data={"title": "Clean grill", "domain": "Household"},
        follow_redirects=True,
    )

    assert create_response.status_code == 200
    assert "Clean grill" in create_response.text

    with client.app.state.session_factory() as session:
        task = session.scalar(select(Task).where(Task.title == "Clean grill"))
        assert task is not None

        task_id = task.id

    assert f'id="task-{task_id}"' in create_response.text
    assert 'id="add-task"' in create_response.text
    assert f'href="/tasks/{task_id}/complete"' in create_response.text
    assert f'action="/tasks/{task_id}/edit"' in create_response.text
    assert f'action="/tasks/{task_id}/delete"' in create_response.text
    assert 'name="domain"' not in create_response.text
    assert "Create a new board item" not in create_response.text

    add_response = client.post(
        f"/tasks/{task_id}/checklist",
        data={"title": "Scrub the grates", "return_to": f"/tasks/{task_id}/complete#checklist"},
        follow_redirects=True,
    )

    assert add_response.status_code == 200
    assert f"Complete Clean grill" in add_response.text

    with client.app.state.session_factory() as session:
        item = session.scalar(select(ChecklistItem).where(ChecklistItem.task_id == task_id))
        assert item is not None
        item_id = item.id
        assert item.title == "Scrub the grates"

    home_response = client.get("/")
    assert f'action="/tasks/{task_id}/checklist"' not in home_response.text
    assert f'action="/tasks/{task_id}/checklist/{item_id}/edit"' not in home_response.text
    assert "Edit checklist" not in home_response.text

    edit_response = client.post(
        f"/tasks/{task_id}/checklist/{item_id}/edit",
        data={
            "title": "Scrub and oil the grates",
            "return_to": f"/tasks/{task_id}/complete#checklist-item-{item_id}",
        },
        follow_redirects=True,
    )

    assert edit_response.status_code == 200
    assert f"Complete Clean grill" in edit_response.text

    with client.app.state.session_factory() as session:
        edited = session.get(ChecklistItem, item_id)
        assert edited.title == "Scrub and oil the grates"

    delete_response = client.post(
        f"/tasks/{task_id}/checklist/{item_id}/delete",
        data={"return_to": f"/tasks/{task_id}/complete#checklist"},
        follow_redirects=True,
    )

    assert delete_response.status_code == 200
    assert f"Complete Clean grill" in delete_response.text

    with client.app.state.session_factory() as session:
        deleted = session.get(ChecklistItem, item_id)
        assert deleted is None

    rename_response = client.post(
        f"/tasks/{task_id}/edit",
        data={"title": "Clean smoker", "return_to": f"/?renamed=1#task-{task_id}"},
        follow_redirects=True,
    )

    assert rename_response.status_code == 200
    assert "Task renamed." in rename_response.text

    with client.app.state.session_factory() as session:
        renamed = session.get(Task, task_id)
        assert renamed is not None
        assert renamed.title == "Clean smoker"

    delete_task_response = client.post(
        f"/tasks/{task_id}/delete",
        data={"return_to": "/?deleted=1"},
        follow_redirects=True,
    )

    assert delete_task_response.status_code == 200
    assert "Task removed." in delete_task_response.text

    with client.app.state.session_factory() as session:
        removed = session.get(Task, task_id)
        assert removed is None


def test_board_shows_recent_completions(client) -> None:
    with client.app.state.session_factory() as session:
        user = User(name="Taylor")
        task = Task(title="Close the office", domain="Office")
        session.add_all([user, task])
        session.flush()
        checklist_item = ChecklistItem(task_id=task.id, title="Lock the doors", sort_order=1)
        session.add(checklist_item)
        session.flush()
        task_run = TaskRun(
            task_id=task.id,
            user_id=user.id,
            task_title_snapshot=task.title,
            user_name_snapshot=user.name,
        )
        session.add(task_run)
        session.flush()
        session.add(
            TaskRunItem(
                task_run_id=task_run.id,
                checklist_item_id=checklist_item.id,
                label=checklist_item.title,
                completed=True,
            )
        )
        session.commit()

    response = client.get("/")

    assert response.status_code == 200
    assert "Recently completed" in response.text
    assert "Close the office" in response.text
    assert "Taylor" in response.text
