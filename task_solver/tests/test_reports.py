from app.models import ChecklistItem, Task, TaskRun, TaskRunItem, User


def test_reports_show_history_and_summaries(client) -> None:
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

    response = client.get("/reports")

    assert response.status_code == 200
    assert "Close the office" in response.text
    assert "Taylor" in response.text
    assert "1 completions" in response.text