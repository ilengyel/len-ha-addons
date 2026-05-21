from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ChecklistItem, Task


DEFAULT_TASKS = [
    ("Wash the dishes", "Household", ["Load dirty dishes", "Run the dishwasher", "Put dishes away"]),
    ("Clean the pool skimmer", "Maintenance", ["Open skimmer lid", "Empty basket", "Re-seat basket"]),
    ("Water indoor plants", "Household", ["Check soil moisture", "Water dry plants", "Empty drip trays"]),
]


def seed_default_data(session: Session) -> None:
    existing_task = session.scalar(select(Task.id).limit(1))
    if existing_task is not None:
        return

    for title, domain, items in DEFAULT_TASKS:
        task = Task(title=title, domain=domain)
        session.add(task)
        session.flush()

        for index, item in enumerate(items, start=1):
            session.add(ChecklistItem(task_id=task.id, title=item, sort_order=index))

    session.commit()
