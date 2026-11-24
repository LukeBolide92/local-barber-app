from typing import Optional
from database import get_session
from models import Client
from sqlalchemy import select, func


def create_client(session, name: str, phone: str, email: str | None = None) -> Client:
    client = Client(name=name, phone=phone, email=email)
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
    client.name = name
    client.phone = phone
    client.email = email
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
    stmt = select(Client).where(
        Client.name.contains(query)
        | Client.phone.contains(query)
        | Client.email.contains(query)
    )
    return list(session.execute(stmt).scalars().all())