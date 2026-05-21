from sqlalchemy import select

from app.models import ChecklistItem, Task, TaskRun, User


def test_complete_task_creates_user_and_run(client) -> None:
    with client.app.state.session_factory() as session:
        task = Task(title="Clean the pool", domain="Maintenance")
        session.add(task)
        session.flush()
        item_one = ChecklistItem(task_id=task.id, title="Skim the leaves", sort_order=1)
        item_two = ChecklistItem(task_id=task.id, title="Check chlorine level", sort_order=2)
        session.add_all([item_one, item_two])
        session.commit()
        task_id = task.id
        item_ids = [item_one.id, item_two.id]

    response = client.post(
        f"/tasks/{task_id}/complete",
        data={
            "existing_user_id": "",
            "new_user_name": "Morgan",
            "completed_item_ids": [str(item_ids[0]), str(item_ids[1])],
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Completion recorded in the backend" in response.text

    with client.app.state.session_factory() as session:
        user = session.scalar(select(User).where(User.name == "Morgan"))
        task_run = session.scalar(select(TaskRun).where(TaskRun.user_name_snapshot == "Morgan"))

        assert user is not None
        assert task_run is not None
        assert task_run.task_title_snapshot == "Clean the pool"
        assert len(task_run.items) == 2


def test_complete_task_requires_all_checklist_items(client) -> None:
    with client.app.state.session_factory() as session:
        task = Task(title="Reset the workshop", domain="Workshop")
        session.add(task)
        session.flush()
        item_one = ChecklistItem(task_id=task.id, title="Return tools", sort_order=1)
        item_two = ChecklistItem(task_id=task.id, title="Sweep the floor", sort_order=2)
        session.add_all([item_one, item_two])
        session.commit()
        task_id = task.id
        item_one_id = item_one.id

    response = client.post(
        f"/tasks/{task_id}/complete",
        data={
            "new_user_name": "Jordan",
            "completed_item_ids": [str(item_one_id)],
        },
    )

    assert response.status_code == 400
    assert "Tick every checklist item" in response.text

    with client.app.state.session_factory() as session:
        task_runs = list(session.scalars(select(TaskRun).where(TaskRun.task_id == task_id)))
        assert task_runs == []
