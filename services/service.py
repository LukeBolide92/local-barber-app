from models import Service
from sqlalchemy import select


def create_service(session, name: str, duration_minutes: int, price: float) -> Service:
    clean_name = name.strip()
    existing = session.execute(
        select(Service).where(Service.name.ilike(clean_name))
    ).scalar_one_or_none()
    if existing:
        raise ValueError(f"Esiste già un servizio con nome '{clean_name}'")

    service = Service(
        name=clean_name,
        duration_minutes=int(duration_minutes),
        price=float(price),
    )
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

    clean_name = name.strip()
    existing = session.execute(
        select(Service).where(Service.name.ilike(clean_name), Service.id != service_id)
    ).scalar_one_or_none()
    if existing:
        raise ValueError(f"Esiste già un servizio con nome '{clean_name}'")

    service.name = clean_name
    service.duration_minutes = int(duration_minutes)
    service.price = float(price)
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
