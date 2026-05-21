from sqlalchemy import select

from app.models import ChecklistItem, Task


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

    client.post(
        f"/tasks/{task_id}/checklist",
        data={"title": "Scrub the grates"},
        follow_redirects=True,
    )

    with client.app.state.session_factory() as session:
        item = session.scalar(select(ChecklistItem).where(ChecklistItem.task_id == task_id))
        assert item is not None
        item_id = item.id
        assert item.title == "Scrub the grates"

    client.post(
        f"/tasks/{task_id}/checklist/{item_id}/edit",
        data={"title": "Scrub and oil the grates"},
        follow_redirects=True,
    )

    with client.app.state.session_factory() as session:
        edited = session.get(ChecklistItem, item_id)
        assert edited.title == "Scrub and oil the grates"

    client.post(f"/tasks/{task_id}/checklist/{item_id}/delete", follow_redirects=True)

    with client.app.state.session_factory() as session:
        deleted = session.get(ChecklistItem, item_id)
        assert deleted is None
