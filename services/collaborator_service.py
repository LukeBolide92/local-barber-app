from datetime import time
import json
from models import Collaborator
from sqlalchemy import select


DEFAULT_WORK_DAYS = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"]


def serialize_work_days(work_days: list[str] | None) -> str:
    return json.dumps(work_days if work_days is not None else DEFAULT_WORK_DAYS)


def deserialize_work_days(work_days_str: str | None) -> list[str]:
    if not work_days_str:
        return list(DEFAULT_WORK_DAYS)
    try:
        data = json.loads(work_days_str)
        return data if isinstance(data, list) else list(DEFAULT_WORK_DAYS)
    except (json.JSONDecodeError, TypeError):
        return list(DEFAULT_WORK_DAYS)


# Backwards-compatible aliases
_serialize_work_days = serialize_work_days
_deserialize_work_days = deserialize_work_days


def create_collaborator(
    session,
    name: str,
    role: str,
    availability: bool = True,
    start_time: time | None = None,
    end_time: time | None = None,
    work_days: list[str] | None = None,
) -> Collaborator:
    clean_name = name.strip()
    existing = session.execute(
        select(Collaborator).where(Collaborator.name.ilike(clean_name))
    ).scalar_one_or_none()
    if existing:
        raise ValueError(f"Esiste già un collaboratore con nome '{clean_name}'")

    collaborator = Collaborator(
        name=clean_name,
        role=role,
        availability=1 if availability else 0,
        start_time=start_time or time(9, 0),
        end_time=end_time or time(18, 0),
        work_days=serialize_work_days(work_days),
    )
    session.add(collaborator)
    session.commit()
    session.refresh(collaborator)
    return collaborator


def get_collaborators(session, only_available: bool = False) -> list[Collaborator]:
    stmt = select(Collaborator).order_by(Collaborator.name)
    if only_available:
        stmt = stmt.where(Collaborator.availability == 1)
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

    clean_name = name.strip()
    existing = session.execute(
        select(Collaborator).where(
            Collaborator.name.ilike(clean_name),
            Collaborator.id != collaborator_id,
        )
    ).scalar_one_or_none()
    if existing:
        raise ValueError(f"Esiste già un collaboratore con nome '{clean_name}'")

    collaborator.name = clean_name
    collaborator.role = role
    collaborator.availability = 1 if availability else 0
    collaborator.start_time = start_time
    collaborator.end_time = end_time
    collaborator.work_days = serialize_work_days(work_days)
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
