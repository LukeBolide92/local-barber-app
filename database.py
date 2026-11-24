from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from contextlib import contextmanager
import os

class Base(DeclarativeBase):
    pass

DB_PATH = "barber.db"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

def init_db():
    """Crea le tabelle se non esistono."""
    from models import Client, Service, Collaborator, Appointment  # noqa: F401
    Base.metadata.create_all(engine)

@contextmanager
def get_session() -> Session:
    """Context manager per sessioni DB."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def get_db_session() -> Session:
    """Restituisce una nuova sessione (da chiudere manualmente)."""
    return SessionLocal()