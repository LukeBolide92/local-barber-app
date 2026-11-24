from typing import Optional
from database import get_session
from models import Service
from sqlalchemy import select


def create_service(session, name: str, duration_minutes: int, price: float) -> Service:
    service = Service(name=name, duration_minutes=duration_minutes, price=price)
    session.add(service)
    session.commit()
    session.refresh(service)
    return service


def get_services(session) -> list[Service]:
    stmt = select(Service).order_by(Service.name)
    return list(session.execute(stmt).scalars().all())


def get_service_by_id(session, service_id: int) -> Service | None:
    stmt = select(Service).where(Service.id == service_id)
    return session.execute(stmt).scalar_one_or_none()


def update_service(
    session, service_id: int, name: str, duration_minutes: int, price: float
) -> Service | None:
    service = get_service_by_id(session, service_id)
    if not service:
        return None
    service.name = name
    service.duration_minutes = duration_minutes
    service.price = price
    session.commit()
    session.refresh(service)
    return service


def delete_service(session, service_id: int) -> bool:
    service = get_service_by_id(session, service_id)
    if not service:
        return False
    session.delete(service)
    session.commit()
    return True