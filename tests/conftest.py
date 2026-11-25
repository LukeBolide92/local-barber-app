import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from models import Appointment, Client, Collaborator, Service  # noqa: F401


@pytest.fixture()
def db_path(tmp_path):
    """Restituisce il percorso di un database SQLite temporaneo isolato."""
    return tmp_path / "test_barber.db"


@pytest.fixture()
def db_session(db_path):
    """Fornisce una sessione SQLAlchemy collegata a un DB temporaneo."""
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
