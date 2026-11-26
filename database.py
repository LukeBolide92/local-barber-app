import os
import logging
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Database path configuration
# Look for environment variable first, then default to data directory relative to app
DB_PATH_ENV = "BARBER_DB_PATH"
DEFAULT_RELATIVE_PATH = "data/barber.db"

# Resolve database path: env var > data directory relative to app source
# This avoids dependency on the execution directory
_app_dir = Path(__file__).parent.resolve()
_default_db = _app_dir / DEFAULT_RELATIVE_PATH

# Ensure the data directory exists
try:
    _default_db.parent.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

DB_PATH = os.environ.get(
    DB_PATH_ENV,
    str(_default_db),
)

logger.info(f"Using database path: {DB_PATH}")

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=False,
    future=True,
)

# Enable SQLite foreign key constraints for all connections
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)


def init_db():
    """Crea le tabelle se non esistono."""
    from models import Client, Service, Collaborator, Appointment  # noqa: F401
    Base.metadata.create_all(engine)
    logger.info("Database tables initialized.")


@contextmanager
def get_session() -> Session:
    """Context manager per sessioni DB con gestione errori e logging."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}", exc_info=True)
        raise
    finally:
        session.close()


def get_db_session() -> Session:
    """Restituisce una nuova sessione (da chiudere manualmente)."""
    return SessionLocal()