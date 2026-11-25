from datetime import date, time, timedelta, datetime
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from models import Appointment, Service, Collaborator


def is_collaborator_available(
    session,
    collaborator_id: int,
    appt_date: date,
    appt_time: time,
) -> bool:
    """Verifica se un collaboratore è disponibile in orario specifico.

    Controlla:
    1. Il collaboratore è attivo (availability=1)
    2. L'orario rientra negli orari di lavoro (start_time - end_time)
    3. Il giorno corrisponde ai giorni di lavoro
    """
    from services.collaborator_service import get_collaborator_by_id as get_collaborator
    collaborator = get_collaborator(session, collaborator_id)
    if not collaborator or collaborator.availability != 1:
        return False

    # Controlla orario di lavoro
    # Normalizza l'orario a un giorno fittizio per il confronto
    appt_time_normalized = time(appt_time.hour, appt_time.minute)
    if collaborator.start_time and collaborator.end_time:
        if appt_time_normalized < collaborator.start_time or appt_time_normalized > collaborator.end_time:
            return False

    # Controlla giorni di lavoro (formato JSON '0,1,2,3,4' per lun-ven)
    if collaborator.work_days:
        import json
        try:
            work_days_list = json.loads(collaborator.work_days)
            # Python datetime weekday: 0=Monday, 6=Sunday
            appt_weekday = appt_date.weekday()
            if appt_weekday not in work_days_list:
                return False
        except (json.JSONDecodeError, TypeError):
            pass

    return True


def check_appointment_conflict(
    session,
    collaborator_id: int,
    appt_date: date,
    appt_time: time,
    duration_minutes: int = 60,
) -> bool:
    """Controlla se c'è un conflitto di appuntamento per il collaboratore.

    Restituisce True se c'è un conflitto, False se l'orario è libero.
    """
    # Calcola l'orario di fine appuntamento
    appt_end = datetime.combine(appt_date, appt_time) + timedelta(minutes=duration_minutes)
    appt_end_time = appt_end.time()

    # Cerca appuntamenti in sovrapposizione per lo stesso collaboratore nello stesso giorno
    stmt = (
        select(Appointment)
        .options(joinedload(Appointment.client), joinedload(Appointment.service))
        .where(Appointment.collaborator_id == collaborator_id)
        .where(Appointment.date == appt_date)
        .order_by(Appointment.time)
    )
    appointments = list(session.execute(stmt).scalars().all())

    # Controlla conflitti: l'orario nuovo deve non sovrapporsi a nessun appuntamento esistente
    for existing in appointments:
        existing_start = existing.time
        # Calcola fine appuntamento esistente basata sulla durata del servizio
        existing_duration = 60  # default 1 ora se non disponibile
        if existing.service:
            existing_duration = existing.service.duration_minutes
        existing_end = datetime.combine(appt_date, existing_start) + timedelta(minutes=existing_duration)

        # Nuovo orario di inizio
        new_start = datetime.combine(appt_date, appt_time)
        # Nuovo orario di fine
        new_end = appt_end

        # Controllo sovrapposizione
        if new_start < existing_end and new_end.time() > existing_start:
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
    # Ottiene la durata del servizio
    from models.service import Service as ServiceModel
    service = session.get(ServiceModel, service_id)
    duration_minutes = service.duration_minutes if service else 60

    # 1. Verifica disponibilità del collaboratore
    if not is_collaborator_available(session, collaborator_id, appt_date, appt_time):
        raise ValueError(f"Collaboratore non disponibile in data {appt_date} alle {appt_time.strftime('%H:%M')}")

    # 2. Verifica conflitto di appuntamento
    if check_appointment_conflict(session, collaborator_id, appt_date, appt_time, duration_minutes):
        raise ValueError("Conflitto di orario: il collaboratore ha già un appuntamento in quel momento")

    appointment = Appointment(
        client_id=client_id,
        service_id=service_id,
        collaborator_id=collaborator_id,
        date=appt_date,
        time=appt_time,
        notes=notes,
    )
    session.add(appointment)
    session.commit()
    session.refresh(appointment)
    return appointment


def get_appointments(
    session,
    date_filter: date | None = None,
    collaborator_id: int | None = None,
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
    return list(session.execute(stmt).scalars().all())


def get_appointments_in_range(
    session,
    start_date: date,
    end_date: date,
    collaborator_id: int | None = None,
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


def delete_appointment(session, appointment_id: int) -> bool:
    appointment = get_appointment_by_id(session, appointment_id)
    if not appointment:
        return False
    session.delete(appointment)
    session.commit()
    return True


def get_appointments_by_date(session, appt_date: date) -> list[Appointment]:
    return get_appointments(session, date_filter=appt_date)


def get_revenue_summary(session) -> dict:
    """Restituisce un dizionario con revenue di oggi e del mese."""
    today = date.today()
    start_month = today.replace(day=1)

    today_appointments = get_appointments_by_date(session, today)
    today_revenue = sum(a.service.price for a in today_appointments if a.service)

    stmt = (
        select(Appointment, Service)
        .join(Service, Appointment.service_id == Service.id)
        .where(Appointment.date >= start_month, Appointment.date <= today)
    )
    month_revenue = sum(
        service.price for _, service in session.execute(stmt).all()
    )

    return {
        "today": float(today_revenue),
        "month": float(month_revenue),
        "today_count": len(today_appointments),
    }