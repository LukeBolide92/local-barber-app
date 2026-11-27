from datetime import datetime
from sqlalchemy.orm import Session
from models import Appointment
from services.appointment_service import get_appointment_by_id


def register_payment(
    session: Session,
    appointment_id: int,
    amount: float,
    method: str,
    payment_datetime: datetime | None = None,
) -> Appointment | None:
    """Registra un pagamento per un appuntamento completato."""
    appointment = get_appointment_by_id(session, appointment_id)
    if not appointment:
        return None

    # Consenti il pagamento solo se l'appuntamento è COMPLETED
    if appointment.status != Appointment.STATUS_COMPLETED:
        raise ValueError(f"Pagamento non consentito: stato '{appointment.status}'")

    if amount <= 0:
        raise ValueError("L'importo deve essere positivo")

    # Registra il pagamento
    appointment.payment_status = Appointment.PAYMENT_PAID
    appointment.amount_paid = amount
    appointment.payment_datetime = payment_datetime or datetime.now()
    appointment.payment_method = method.strip()

    session.commit()
    session.refresh(appointment)
    return appointment


def register_refund(
    session: Session,
    appointment_id: int,
) -> Appointment | None:
    """Registra un rimborso per un appuntamento completato."""
    appointment = get_appointment_by_id(session, appointment_id)
    if not appointment:
        return None

    # Consenti il rimborso solo se l'appuntamento è COMPLETED
    if appointment.status != Appointment.STATUS_COMPLETED:
        raise ValueError(f"Rimborso non consentito: stato '{appointment.status}'")

    if appointment.payment_status == Appointment.PAYMENT_REFUNDED:
        raise ValueError("Appuntamento già rimborsato")

    appointment.payment_status = Appointment.PAYMENT_REFUNDED
    session.commit()
    session.refresh(appointment)
    return appointment


def get_payment_details(
    session: Session,
    appointment_id: int,
) -> dict | None:
    """Restituisce i dettagli del pagamento per un appuntamento."""
    appointment = get_appointment_by_id(session, appointment_id)
    if not appointment:
        return None

    return {
        "payment_status": appointment.payment_status,
        "amount_paid": appointment.amount_paid,
        "payment_datetime": appointment.payment_datetime,
        "payment_method": appointment.payment_method,
    }
