from datetime import date, time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_session
from models import Appointment, Client, Collaborator, Service  # noqa: F401
from services.appointment_service import (
    get_appointment_by_id,
    complete_appointment,
    create_appointment,
)
from services.client_service import create_client, get_clients
from services.collaborator_service import create_collaborator
from services.payment_service import register_payment, register_refund
from services.service import create_service


@pytest.fixture()
def engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'tx_barber.db'}", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def session_factory(engine):
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    return Session


def _create_completed_unpaid(session) -> Appointment:
    collab = create_collaborator(
        session,
        "Mario",
        "Barbiere",
        True,
        time(9, 0),
        time(18, 0),
        ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"],
    )
    service = create_service(session, "Taglio", 30, 20.0)
    client = create_client(session, "Luca", "333000111")
    appt = create_appointment(session, client.id, service.id, collab.id, date(2025, 1, 6), time(10, 0))
    complete_appointment(session, appt.id)
    return appt


class TestTransactionManagement:
    def test_failed_payment_registration_keeps_consistent_state(self, session_factory):
        """TASK 5: registrazione pagamento fallita -> rollback -> stato coerente."""
        with get_session(session_factory=session_factory) as session:
            appt = _create_completed_unpaid(session)

            with pytest.raises(ValueError):
                register_payment(session, appt.id, amount=0.0, method="Contanti")

        with get_session(session_factory=session_factory) as session:
            reloaded = get_appointment_by_id(session, appt.id)
            assert reloaded.status == Appointment.STATUS_COMPLETED
            assert reloaded.payment_status == Appointment.PAYMENT_UNPAID

    def test_get_session_rolls_back_on_error(self, engine, session_factory):
        """TASK 5: rollback in caso di errore all'interno del context manager."""
        with pytest.raises(RuntimeError):
            with get_session(session_factory=session_factory) as session:
                session.add(Client(name="Mario Rossi", phone="333000111"))
                raise RuntimeError("boom")

        with get_session(session_factory=session_factory) as session:
            assert len(get_clients(session)) == 0

    def test_quick_complete_and_register_payment_coherent(self, session_factory):
        """TASK 5: operazione rapida completa + registra pagamento -> coerenza stato."""
        from services.payment_service import complete_appointment_and_register_quick_payment

        with get_session(session_factory=session_factory) as session:
            appt = _create_completed_unpaid(session)
            result = complete_appointment_and_register_quick_payment(session, appt.id, amount=20.0, method="Contanti")
            assert result is not None
            assert result.status == Appointment.STATUS_COMPLETED
            assert result.payment_status == Appointment.PAYMENT_PAID

    def test_multiple_operations_same_transaction(self, session_factory):
        """TASK 5: più operazioni eseguite nella stessa sessione vengono committate in modo coerente."""
        from services.payment_service import complete_appointment_and_register_quick_payment

        with get_session(session_factory=session_factory) as session:
            appt = _create_completed_unpaid(session)
            complete_appointment_and_register_quick_payment(session, appt.id, amount=20.0, method="Contanti")
            current = get_appointment_by_id(session, appt.id)
            assert current.payment_status == Appointment.PAYMENT_PAID
