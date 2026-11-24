from typing import Optional
from datetime import time
import json
from database import get_session
from models import Collaborator
from sqlalchemy import select


def _serialize_work_days(work_days: list[str] | None) -> str | None:
    if work_days is None:
        return None
    return json.dumps(work_days)


def _deserialize_work_days(work_days_str: str | None) -> list[str]:
    if not work_days_str:
        return ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"]
    try:
        return json.loads(work_days_str)
    except (json.JSONDecodeError, TypeError):
        return ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"]


def create_collaborator(
    session,
    name: str,
    role: str,
    availability: bool = True,
    start_time: time | None = None,
    end_time: time | None = None,
    work_days: list[str] | None = None,
) -> Collaborator:
    collaborator = Collaborator(
        name=name,
        role=role,
        availability=1 if availability else 0,
        start_time=start_time or time(9, 0),
        end_time=end_time or time(18, 0),
        work_days=_serialize_work_days(work_days),
    )
    session.add(collaborator)
    session.commit()
    session.refresh(collaborator)
    return collaborator


def get_collaborators(session) -> list[Collaborator]:
    stmt = select(Collaborator).order_by(Collaborator.name)
    return list(session.execute(stmt).scalars().all())


def get_collaborator_by_id(session, collaborator_id: int) -> Collaborator | None:
    stmt = select(Collaborator).where(Collaborator.id == collaborator_id)
    return session.execute(stmt).scalar_one_or_none()


def update_collaborator(
    session,
    collaborator_id: int,
    name: str,
    role: str,
    availability: bool,
    start_time: time,
    end_time: time,
    work_days: list[str],
) -> Collaborator | None:
    collaborator = get_collaborator_by_id(session, collaborator_id)
    if not collaborator:
        return None
    collaborator.name = name
    collaborator.role = role
    collaborator.availability = 1 if availability else 0
    collaborator.start_time = start_time
    collaborator.end_time = end_time
    collaborator.work_days = _serialize_work_days(work_days)
    session.commit()
    session.refresh(collaborator)
    return collaborator


def delete_collaborator(session, collaborator_id: int) -> bool:
    collaborator = get_collaborator_by_id(session, collaborator_id)
    if not collaborator:
        return False
    session.delete(collaborator)
    session.commit()
    return True