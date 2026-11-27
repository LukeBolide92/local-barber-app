from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from database import Base, _add_payment_columns_if_missing
from models import Appointment  # noqa: F401


PAYMENT_COLUMNS = ("payment_status", "amount_paid", "payment_datetime", "payment_method")


def _make_session_factory(engine):
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    return Session


def _seed_appointments(engine, statuses_prices):
    """Inserisce appuntamenti di esempio (status, price) nello schema vecchio."""
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO clients (id, name, phone, email) VALUES (1, 'Luca', '333000111', 'luca@example.com')"
            )
        )
        conn.execute(
            text("INSERT INTO services (id, name, duration_minutes, price) VALUES (1, 'Taglio', 30, 25.0)")
        )
        conn.execute(
            text(
                "INSERT INTO collaborators (id, name, role, availability, start_time, end_time, work_days) "
                "VALUES (1, 'Mario', 'Barbiere', 1, '09:00', '18:00', NULL)"
            )
        )
        for status, price in statuses_prices:
            conn.execute(
                text(
                    """
                    INSERT INTO appointments (client_id, service_id, collaborator_id, date, time, notes, status, price, duration_minutes)
                    VALUES (1, 1, 1, '2025-01-06', '10:00:00', 'note', :status, :price, 30)
                    """
                ),
                {"status": status, "price": price},
            )


def _get_appointments(engine):
    Session = _make_session_factory(engine)
    session = Session()
    try:
        return session.query(Appointment).all()
    finally:
        session.close()


def _make_old_schema_engine(tmp_path):
    """Crea un database SQLite con lo schema precedente alla migrazione pagamenti:
    la tabella appointments esiste ma senza le colonne di pagamento."""
    engine = create_engine(f"sqlite:///{tmp_path / 'old_barber.db'}", echo=False)
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        for column in PAYMENT_COLUMNS:
            conn.execute(text(f"ALTER TABLE appointments DROP COLUMN {column}"))
    return engine


def _run_migration(engine):
    _add_payment_columns_if_missing(engine=engine, session_factory=_make_session_factory(engine))


class TestPaymentMigrationBackfill:
    def test_completed_appointment_is_migrated_to_paid(self, tmp_path):
        engine = _make_old_schema_engine(tmp_path)
        try:
            _seed_appointments(engine, [("COMPLETED", 25.0)])
            _run_migration(engine)

            appts = _get_appointments(engine)
            assert len(appts) == 1
            appt = appts[0]
            assert appt.status == Appointment.STATUS_COMPLETED
            # Lo stato di pagamento deve essere quello corretto (PAID), non lo stato dell'appuntamento
            assert appt.payment_status == Appointment.PAYMENT_PAID
            assert appt.amount_paid == 25.0
            assert appt.payment_status in Appointment.VALID_PAYMENT_STATUSES
        finally:
            engine.dispose()

    def test_incomplete_appointment_is_migrated_to_unpaid(self, tmp_path):
        engine = _make_old_schema_engine(tmp_path)
        try:
            _seed_appointments(engine, [("BOOKED", 25.0)])
            _run_migration(engine)

            appts = _get_appointments(engine)
            assert len(appts) == 1
            appt = appts[0]
            assert appt.status == Appointment.STATUS_BOOKED
            # Un appuntamento non completato non deve essere trasformato arbitrariamente in pagato
            assert appt.payment_status == Appointment.PAYMENT_UNPAID
            assert appt.amount_paid == 0.0
            assert appt.payment_status in Appointment.VALID_PAYMENT_STATUSES
        finally:
            engine.dispose()

    def test_migration_is_idempotent(self, tmp_path):
        engine = _make_old_schema_engine(tmp_path)
        try:
            _seed_appointments(engine, [("COMPLETED", 25.0), ("BOOKED", 25.0)])

            _run_migration(engine)
            first_run = _get_appointments(engine)

            # Seconda esecuzione della migrazione: le colonne ora esistono -> skip
            _run_migration(engine)
            second_run = _get_appointments(engine)

            assert len(first_run) == len(second_run) == 2
            completed = [a for a in second_run if a.status == Appointment.STATUS_COMPLETED][0]
            booked = [a for a in second_run if a.status == Appointment.STATUS_BOOKED][0]
            assert completed.payment_status == Appointment.PAYMENT_PAID
            assert booked.payment_status == Appointment.PAYMENT_UNPAID
        finally:
            engine.dispose()

    def test_migration_does_not_overwrite_existing_valid_data(self, tmp_path):
        """Su un DB già migrato, la migrazione non deve sovrascrivere dati validi esistenti."""
        engine = create_engine(f"sqlite:///{tmp_path / 'migrated_barber.db'}", echo=False)
        Base.metadata.create_all(engine)  # schema già migrato (colonne pagamento presenti)
        try:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "INSERT INTO clients (id, name, phone, email) VALUES (1, 'Luca', '333000111', 'luca@example.com')"
                    )
                )
                conn.execute(
                    text("INSERT INTO services (id, name, duration_minutes, price) VALUES (1, 'Taglio', 30, 25.0)")
                )
                conn.execute(
                    text(
                        "INSERT INTO collaborators (id, name, role, availability, start_time, end_time, work_days) "
                        "VALUES (1, 'Mario', 'Barbiere', 1, '09:00', '18:00', NULL)"
                    )
                )
                conn.execute(
                    text(
                        """
                        INSERT INTO appointments (client_id, service_id, collaborator_id, date, time, notes, status, price, duration_minutes, payment_status, amount_paid, payment_datetime, payment_method)
                        VALUES (1, 1, 1, '2025-01-06', '10:00:00', 'note', 'COMPLETED', 25.0, 30, 'PAID', 25.0, NULL, 'Contanti')
                        """
                    )
                )

            _run_migration(engine)

            appts = _get_appointments(engine)
            assert len(appts) == 1
            assert appts[0].payment_status == "PAID"
            assert appts[0].amount_paid == 25.0
        finally:
            engine.dispose()
