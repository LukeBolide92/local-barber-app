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
DEFAULT_RELATIVE_PATH = "../data/barber.db"

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


def _add_payment_columns_if_missing(engine=engine, session_factory=None) -> None:
    """Aggiunge colonne di pagamento se mancano nel database esistente.

    Esegue un backfill sensato dei dati esistenti:
    - Appuntamenti COMPLETED: imposta payment_status=PAID con amount_paid=price
    - Altri appuntamenti: imposta payment_status=UNPAID
    """
    from models import Appointment

    from sqlalchemy import inspect as sa_inspect, text

    inspector = sa_inspect(engine)
    cols = [c['name'] for c in inspector.get_columns('appointments')]
    payment_columns = ['payment_status', 'amount_paid', 'payment_datetime', 'payment_method']
    missing_columns = [c for c in payment_columns if c not in cols]
    if not missing_columns:
        logger.info("Columnes di pagamento già presenti. Skip migration.")
        return

    stmts = {
        'payment_status': text("ALTER TABLE appointments ADD COLUMN payment_status TEXT DEFAULT 'UNPAID'"),
        'amount_paid': text("ALTER TABLE appointments ADD COLUMN amount_paid REAL"),
        'payment_datetime': text("ALTER TABLE appointments ADD COLUMN payment_datetime DATETIME"),
        'payment_method': text("ALTER TABLE appointments ADD COLUMN payment_method TEXT"),
    }

    with engine.begin() as conn:
        for column in missing_columns:
            conn.execute(stmts[column])

    # Backfill dei dati esistenti
    _session_factory = session_factory or SessionLocal
    with _session_factory() as session:
        appointments = session.query(Appointment).all()
        for appt in appointments:
            if appt.status == Appointment.STATUS_COMPLETED:
                appt.payment_status = Appointment.PAYMENT_PAID
                appt.amount_paid = appt.price if appt.price else 0.0
                # Imposta data/pagamento alla data/ora dell'appuntamento
                from datetime import datetime
                appt.payment_datetime = datetime.combine(appt.date, appt.time)
                if appt.service:
                    appt.payment_method = "Contanti"
                else:
                    appt.payment_method = "Altro"
            else:
                appt.payment_status = Appointment.PAYMENT_UNPAID
                appt.amount_paid = 0.0
        session.commit()
    logger.info(f"Migrazione pagamento completata per {len(appointments)} appuntamenti.")


def init_db():
    """Crea le tabelle se non esistono e migra colonne di pagamento."""
    from models import Client, Service, Collaborator, Appointment  # noqa: F401
    Base.metadata.create_all(engine)
    # Esegui migrazione colonne esistenti
    _add_payment_columns_if_missing()
    logger.info("Database tables initialized and migrated.")


@contextmanager
def get_session(session_factory=None) -> Session:
    """Context manager per sessioni DB con gestione errori e logging."""
    session = (session_factory or SessionLocal)()
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