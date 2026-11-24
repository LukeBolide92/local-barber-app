from models import Client
from sqlalchemy import select, func


def create_client(session, name: str, phone: str, email: str | None = None) -> Client:
    client = Client(
        name=name.strip(),
        phone=phone.strip(),
        email=email.strip() if email and email.strip() else None,
    )
    session.add(client)
    session.commit()
    session.refresh(client)
    return client


def get_clients(session) -> list[Client]:
    stmt = select(Client).order_by(Client.name)
    return list(session.execute(stmt).scalars().all())


def get_client_by_id(session, client_id: int) -> Client | None:
    stmt = select(Client).where(Client.id == client_id)
    return session.execute(stmt).scalar_one_or_none()


def update_client(
    session, client_id: int, name: str, phone: str, email: str | None = None
) -> Client | None:
    client = get_client_by_id(session, client_id)
    if not client:
        return None
    client.name = name.strip()
    client.phone = phone.strip()
    client.email = email.strip() if email and email.strip() else None
    session.commit()
    session.refresh(client)
    return client


def delete_client(session, client_id: int) -> bool:
    client = get_client_by_id(session, client_id)
    if not client:
        return False
    session.delete(client)
    session.commit()
    return True


def search_clients(session, query: str) -> list[Client]:
    q = query.strip()
    if not q:
        return get_clients(session)
    stmt = (
        select(Client)
        .where(
            Client.name.ilike(f"%{q}%")
            | Client.phone.ilike(f"%{q}%")
            | func.coalesce(Client.email, "").ilike(f"%{q}%")
        )
        .order_by(Client.name)
    )
    return list(session.execute(stmt).scalars().all())
