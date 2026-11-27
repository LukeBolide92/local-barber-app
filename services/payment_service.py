from datetime import datetime
from sqlalchemy.orm import Session
from models import Appointment
from services.appointment_service import complete_appointment, get_appointment_by_id


def _validate_payment_for_registration(appointment: Appointment, amount: float) -> None:
    """Validazioni comuni per la registrazione di un pagamento (sul livello ORM, senza commit)."""
    # Consenti il pagamento solo se l'appuntamento è COMPLETED
    if appointment.status != Appointment.STATUS_COMPLETED:
        raise ValueError(f"Pagamento non consentito: stato '{appointment.status}'")

    if amount <= 0:
        raise ValueError("L'importo deve essere positivo")

    # TASK 2: non è possibile registrare un pagamento se l'appuntamento è già pagato o rimborsato
    if appointment.payment_status == Appointment.PAYMENT_PAID:
        raise ValueError("Pagamento già registrato per questo appuntamento")
    if appointment.payment_status == Appointment.PAYMENT_REFUNDED:
        raise ValueError("Impossibile registrare un pagamento per un appuntamento rimborsato")


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

    _validate_payment_for_registration(appointment, amount)

    # Registra il pagamento
    appointment.payment_status = Appointment.PAYMENT_PAID
    appointment.amount_paid = amount
    appointment.payment_datetime = payment_datetime or datetime.now()
    appointment.payment_method = method.strip()

    session.commit()
    session.refresh(appointment)
    return appointment


def complete_appointment_and_register_quick_payment(
    session: Session,
    appointment_id: int,
    amount: float,
    method: str,
    payment_datetime: datetime | None = None,
) -> Appointment | None:
    """Operazione rapida: completa l'appuntamento e registra contestivamente il pagamento (es. contanti).

    TASK 4 (FASE 4.2): l'operazione è ATOMA - completamento e registrazione avvengono
    nella stessa transazione senza commit intermedi: in caso di errore nessun commit viene
    eseguito e il completamento viene annullato insieme al pagamento.
    """
    appointment = get_appointment_by_id(session, appointment_id)
    if not appointment:
        return None

    # Completamento dell'appuntamento
    if appointment.status in (Appointment.STATUS_CANCELLED, Appointment.STATUS_NO_SHOW):
        return None
    if appointment.service and appointment.price is None:
        appointment.price = appointment.service.price
    appointment.status = Appointment.STATUS_COMPLETED

    # Registrazione del pagamento contestiva al completamento
    _validate_payment_for_registration(appointment, amount)
    appointment.payment_status = Appointment.PAYMENT_PAID
    appointment.amount_paid = amount
    appointment.payment_datetime = payment_datetime or datetime.now()
    appointment.payment_method = method.strip()

    # Transazione unica per completamento + pagamento
    session.commit()
    session.refresh(appointment)
    return appointment


def register_refund(
    session: Session,
    appointment_id: int,
    amount: float | None = None,
) -> Appointment | None:
    """Registra un rimborso per un appuntamento completato.

    TASK 3: sicurezza dei rimborsi - il rimborso è consentito solo per appuntamenti
    pagati; l'importo non può superare quello già incassato.

    TASK 2 (FASE 4.2): supporto esclusivamente a rimborsi totali. Qualsiasi importo
    diverso dall'importo effettivamente pagato viene rifiutato come rimborso parziale.
    """
    appointment = get_appointment_by_id(session, appointment_id)
    if not appointment:
        return None

    # Consenti il rimborso solo se l'appuntamento è COMPLETED
    if appointment.status != Appointment.STATUS_COMPLETED:
        raise ValueError(f"Rimborso non consentito: stato '{appointment.status}'")

    if appointment.payment_status == Appointment.PAYMENT_REFUNDED:
        raise ValueError("Appuntamento già rimborsato")

    # TASK 3: il rimborso è consentito solo per appuntamenti effettivamente pagati
    if appointment.payment_status != Appointment.PAYMENT_PAID:
        raise ValueError(f"Rimborso non consentito: appuntamento non pagato (stato pagamento: '{appointment.payment_status}')")

    amount_paid = float(appointment.amount_paid or 0.0)
    refund_amount = float(amount) if amount is not None else amount_paid
    if refund_amount > amount_paid + 1e-9:
        raise ValueError("Importo di rimborso superiore all'importo incassato")
    # TASK 2 (FASE 4.2): supporto esclusivamente a rimborsi totali
    if amount is not None and abs(refund_amount - amount_paid) > 1e-9:
        raise ValueError("Rimborso parziale non consentito: per questa versione supportiamo solo rimborsi totali")

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
