from datetime import date, time, timedelta, datetime
from sqlalchemy import select, case, func
from sqlalchemy.orm import joinedload
from models import Appointment, Service, Collaborator


def is_collaborator_available(
    session,
    collaborator_id: int,
    appt_date: date,
    appt_time: time,
    duration_minutes: int = 60,
) -> bool:
    """Verifica se un collaboratore è disponibile in orario specifico.

    Controlla:
    1. Il collaboratore è attivo (availability=1)
    2. L'orario di inizio e quello di fine dell'intervallo rientrano negli orari di lavoro (start_time - end_time)
    3. Il giorno corrisponde ai giorni di lavoro
    4. Non ci sono sovrapposizioni con altri appuntamenti BOOKED
    """
    from services.collaborator_service import get_collaborator_by_id as get_collaborator
    collaborator = get_collaborator(session, collaborator_id)
    if not collaborator or collaborator.availability != 1:
        return False

    # Controlla orario di lavoro: inizio e fine dell'intervallo devono rientrare nel turno
    start_time = collaborator.start_time
    end_time = collaborator.end_time
    if start_time and end_time:
        start_dt = datetime.combine(appt_date, appt_time)
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        if appt_time < start_time or end_dt.time() > end_time:
            return False

    # Controlla giorni di lavoro (supporta sia nomi italiani es. ["Lunedì", ...] sia indici 0..6)
    if collaborator.work_days:
        import json
        weekday_names = [
            "lunedì",
            "martedì",
            "mercoledì",
            "giovedì",
            "venerdì",
            "sabato",
            "domenica",
        ]
        try:
            work_days_list = json.loads(collaborator.work_days)
            if isinstance(work_days_list, list):
                appt_weekday = appt_date.weekday()
                appt_day_name = weekday_names[appt_weekday]
                normalized_days = {
                    str(d).strip().lower() for d in work_days_list
                }
                if (
                    str(appt_weekday) not in normalized_days
                    and appt_day_name not in normalized_days
                ):
                    return False
        except (json.JSONDecodeError, TypeError):
            pass

    # Controlla sovrapposizioni con altri appuntamenti BOOKED
    if check_appointment_conflict(session, collaborator_id, appt_date, appt_time, duration_minutes):
        return False

    return True


def check_appointment_conflict(
    session,
    collaborator_id: int,
    appt_date: date,
    appt_time: time,
    duration_minutes: int = 60,
) -> bool:
    """Controlla se c'è un conflitto di appuntamento per il collaboratore.

    Solo gli appuntamenti in stato BOOKED interferiscono con la disponibilità.
    Appuntamenti completati, cancellati o assenti non occupano il tempo.

    Restituisce True se c'è un conflitto, False se l'orario è libero.
    """
    # Calcola l'orario di fine appuntamento
    appt_end = datetime.combine(appt_date, appt_time) + timedelta(minutes=duration_minutes)
    appt_end_time = appt_end.time()

    # Cerca appuntamenti in stato BOOKED per il collaboratore nello stesso giorno
    stmt = (
        select(Appointment)
        .options(joinedload(Appointment.client), joinedload(Appointment.service))
        .where(Appointment.collaborator_id == collaborator_id)
        .where(Appointment.date == appt_date)
        .where(Appointment.status == Appointment.STATUS_BOOKED)
        .order_by(Appointment.time)
    )
    appointments = list(session.execute(stmt).scalars().all())

    # Controlla conflitti: l'orario nuovo deve non sovrapporsi a nessun appuntamento BOOKED esistente
    for existing in appointments:
        existing_start_dt = datetime.combine(appt_date, existing.time)
        # Calcola fine appuntamento esistente basata sulla durata
        existing_duration = existing.duration_minutes if existing.duration_minutes else (
            existing.service.duration_minutes if existing.service else 60
        )
        existing_end = existing_start_dt + timedelta(minutes=existing_duration)

        # Nuovo orario di inizio e fine
        new_start = datetime.combine(appt_date, appt_time)
        new_end = appt_end

        # Controllo sovrapposizione
        if new_start < existing_end and new_end > existing_start_dt:
            return True  # Conflitto rilevato

    return False


def create_appointment(
    session,
    client_id: int,
    service_id: int,
    collaborator_id: int,
    appt_date: date,
    appt_time: time,
    notes: str | None = None,
) -> Appointment:
    # Ottiene la durata e il prezzo del servizio
    from models.service import Service as ServiceModel
    service = session.get(ServiceModel, service_id)
    duration_minutes = service.duration_minutes if service else 60
    price = service.price if service else 0.0

    # 1. Verifica conflitto di appuntamento (solo appuntamenti BOOKED)
    if check_appointment_conflict(session, collaborator_id, appt_date, appt_time, duration_minutes):
        raise ValueError("Conflitto di orario: il collaboratore ha già un appuntamento in quel momento")

    # 2. Verifica disponibilità del collaboratore (orario di lavoro + intervallo)
    if not is_collaborator_available(session, collaborator_id, appt_date, appt_time, duration_minutes):
        raise ValueError(f"Collaboratore non disponibile in data {appt_date} alle {appt_time.strftime('%H:%M')}")

    appointment = Appointment(
        client_id=client_id,
        service_id=service_id,
        collaborator_id=collaborator_id,
        date=appt_date,
        time=appt_time,
        notes=notes,
        status=Appointment.STATUS_BOOKED,
        price=price,
        duration_minutes=duration_minutes,
    )
    session.add(appointment)
    session.commit()
    session.refresh(appointment)
    return appointment


def get_appointments(
    session,
    date_filter: date | None = None,
    collaborator_id: int | None = None,
    status_filter: str | None = None,
) -> list[Appointment]:
    stmt = (
        select(Appointment)
        .options(
            joinedload(Appointment.client),
            joinedload(Appointment.service),
            joinedload(Appointment.collaborator),
        )
        .order_by(Appointment.date, Appointment.time)
    )
    if date_filter is not None:
        stmt = stmt.where(Appointment.date == date_filter)
    if collaborator_id is not None:
        stmt = stmt.where(Appointment.collaborator_id == collaborator_id)
    if status_filter is not None:
        stmt = stmt.where(Appointment.status == status_filter)
    return list(session.execute(stmt).scalars().all())


def get_appointments_in_range(
    session,
    start_date: date,
    end_date: date,
    collaborator_id: int | None = None,
    status_filter: str | None = None,
) -> list[Appointment]:
    stmt = (
        select(Appointment)
        .options(
            joinedload(Appointment.client),
            joinedload(Appointment.service),
            joinedload(Appointment.collaborator),
        )
        .where(Appointment.date >= start_date, Appointment.date <= end_date)
        .order_by(Appointment.date, Appointment.time)
    )
    if collaborator_id is not None:
        stmt = stmt.where(Appointment.collaborator_id == collaborator_id)
    if status_filter is not None:
        stmt = stmt.where(Appointment.status == status_filter)
    return list(session.execute(stmt).scalars().all())


def get_appointment_by_id(session, appointment_id: int) -> Appointment | None:
    stmt = (
        select(Appointment)
        .options(
            joinedload(Appointment.client),
            joinedload(Appointment.service),
            joinedload(Appointment.collaborator),
        )
        .where(Appointment.id == appointment_id)
    )
    return session.execute(stmt).scalar_one_or_none()


def update_appointment(
    session,
    appointment_id: int,
    date: date | None = None,
    time: time | None = None,
    notes: str | None = None,
    status: str | None = None,
) -> Appointment | None:
    """Modifica un appuntamento esistente."""
    appointment = get_appointment_by_id(session, appointment_id)
    if not appointment:
        return None

    if date is not None:
        appointment.date = date
    if time is not None:
        appointment.time = time
    if notes is not None:
        appointment.notes = notes
    if status is not None:
        # Validare che lo stato sia uno stato valido
        if status in Appointment.VALID_STATUSES:
            appointment.status = status
            # TASK 3: se lo stato non è COMPLETED, il pagamento torna a UNPAID
            if status != Appointment.STATUS_COMPLETED:
                appointment.payment_status = Appointment.PAYMENT_UNPAID
                appointment.amount_paid = 0.0
                appointment.payment_datetime = None
                appointment.payment_method = None
        else:
            raise ValueError(f"Stato non valido: {status}")

    session.commit()
    session.refresh(appointment)
    return appointment


def cancel_appointment(session, appointment_id: int) -> bool:
    """Annulla un appuntamento (stato CANCELLED)."""
    appointment = get_appointment_by_id(session, appointment_id)
    if not appointment:
        return False

    # Non si può annullare un appuntamento già completato o assente
    if appointment.status in (Appointment.STATUS_COMPLETED, Appointment.STATUS_NO_SHOW):
        return False

    appointment.status = Appointment.STATUS_CANCELLED
    # TASK 3: annullato -> pagamento torna a UNPAID
    appointment.payment_status = Appointment.PAYMENT_UNPAID
    appointment.amount_paid = 0.0
    appointment.payment_datetime = None
    appointment.payment_method = None
    session.commit()
    return True


def complete_appointment(
    session,
    appointment_id: int,
    recorded_price: float | None = None,
) -> Appointment | None:
    """Completa un appuntamento (stato COMPLETED).

    L'appuntamento completato conserva il prezzo e la durata originari
    del servizio, anche se il servizio viene successivamente modificato.
    """
    appointment = get_appointment_by_id(session, appointment_id)
    if not appointment:
        return None

    # Non si può completare un appuntamento già cancellato o assente
    if appointment.status in (Appointment.STATUS_CANCELLED, Appointment.STATUS_NO_SHOW):
        return None

    # Conserva il prezzo originario: se non è stato registrato un prezzo specifico,
    # usa il prezzo corrente del servizio (ma salvalo per riferimento futuro)
    if recorded_price is not None:
        appointment.price = recorded_price
    elif appointment.service and appointment.price is None:
        appointment.price = appointment.service.price

    appointment.status = Appointment.STATUS_COMPLETED
    # TASK 2: separazione completamento/pagamento - il completamento non registra automaticamente il pagamento.
    # I dati economici non vengono modificati qui: il pagamento va registrato tramite register_payment (o l'operazione rapida).

    session.commit()
    session.refresh(appointment)
    return appointment


def register_no_show(session, appointment_id: int) -> bool:
    """Registra che il cliente non si è presentato (stato NO_SHOW)."""
    appointment = get_appointment_by_id(session, appointment_id)
    if not appointment:
        return False

    # Non si può registrare NO_SHOW per un appuntamento già completato o cancellato
    if appointment.status in (Appointment.STATUS_COMPLETED, Appointment.STATUS_CANCELLED):
        return False

    appointment.status = Appointment.STATUS_NO_SHOW
    # TASK 3: assente -> pagamento torna a UNPAID
    appointment.payment_status = Appointment.PAYMENT_UNPAID
    appointment.amount_paid = 0.0
    appointment.payment_datetime = None
    appointment.payment_method = None
    session.commit()
    return True


def delete_appointment(session, appointment_id: int) -> bool:
    """Elimina fisicamente un appuntamento dal database."""
    appointment = get_appointment_by_id(session, appointment_id)
    if not appointment:
        return False
    session.delete(appointment)
    session.commit()
    return True


def get_appointments_by_date(session, appt_date: date) -> list[Appointment]:
    return get_appointments(session, date_filter=appt_date)


def get_appointment_net_revenue(appointment: Appointment) -> float:
    """Calcola l'importo netto di incasso per un singolo appuntamento.

    Regole TASK 3:
    - Solo appuntamenti COMPLETED generano incassi.
    - Solo pagamenti PAID generano incassi (UNPAID non incassa).
    - I rimborsi (REFUNDED) annullano l'incasso: il netto diventa 0.
    """
    if appointment.status != Appointment.STATUS_COMPLETED:
        return 0.0
    if appointment.payment_status == Appointment.PAYMENT_REFUNDED:
        # Il rimborso annulla l'incasso: netto = 0
        return 0.0
    if appointment.payment_status == Appointment.PAYMENT_PAID:
        # Incasso effettivamente registrato e pagato
        return float(appointment.amount_paid or 0.0)
    # UNPAID: nessun incasso registrato
    return 0.0


def get_revenue_between(session, start_date, end_date) -> float:
    """Restituisce l'incasso netto (incassi meno rimborsi) per un intervallo di date."""
    from sqlalchemy import func
    stmt = (
        select(Appointment)
        .where(
            Appointment.date >= start_date,
            Appointment.date <= end_date,
            Appointment.status == Appointment.STATUS_COMPLETED,
        )
    )
    appointments = list(session.execute(stmt).scalars().all())
    return round(sum(get_appointment_net_revenue(a) for a in appointments), 2)


def get_revenue_summary(session) -> dict:
    """Restituisce un dizionario con revenue di oggi e del mese.

    TASK 3: considera solo appuntamenti COMPLETED con pagamento PAID come incassi.
    Gestisce i rimborsi (REFUNDED) sottraendo gli importi rimborsati.
    """
    today = date.today()
    start_month = today.replace(day=1)

    # Incassi di oggi: solo appuntamenti completati e pagati
    today_revenue = get_revenue_between(session, today, today)

    # Incassi mese: solo appuntamenti completati e pagati nel mese corrente
    month_revenue = get_revenue_between(session, start_month, today)

    # Conteggio appuntamenti di oggi pagati (completati e pagati)
    today_count_result = (
        session.query(func.count(Appointment.id))
        .filter(
            Appointment.date == today,
            Appointment.status == Appointment.STATUS_COMPLETED,
            Appointment.payment_status == Appointment.PAYMENT_PAID,
        )
        .scalar()
    )
    today_count = today_count_result if today_count_result else 0

    # Conteggio appuntamenti completati oggi (tutti, anche non pagati)
    today_completed_count_result = (
        session.query(func.count(Appointment.id))
        .filter(
            Appointment.date == today,
            Appointment.status == Appointment.STATUS_COMPLETED,
        )
        .scalar()
    )
    today_completed_count = today_completed_count_result if today_completed_count_result else 0

    return {
        "today": today_revenue,
        "month": month_revenue,
        "today_count": today_count,
        "today_completed_count": today_completed_count,
    }