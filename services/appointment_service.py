from datetime import date, time
from typing import Optional
from sqlalchemy import select, func
from database import get_session
from models import Appointment, Client, Service, Collaborator


def create_appointment(
    session,
    client_id: int,
    service_id: int,
    collaborator_id: int,
    appt_date: date,
    appt_time: time,
    notes: str | None = None,
) -> Appointment:
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


def get_appointments(session, date_filter: date | None = None) -> list[Appointment]:
    stmt = select(Appointment).order_by(Appointment.date, Appointment.time)
    if date_filter:
        stmt = stmt.where(Appointment.date == date_filter)
    return list(session.execute(stmt).scalars().all())


def get_appointment_by_id(session, appointment_id: int) -> Appointment | None:
    stmt = select(Appointment).where(Appointment.id == appointment_id)
    return session.execute(stmt).scalar_one_or_none()


def delete_appointment(session, appointment_id: int) -> bool:
    appointment = get_appointment_by_id(session, appointment_id)
    if not appointment:
        return False
    session.delete(appointment)
    session.commit()
    return True


def get_appointments_by_date(session, appt_date: date) -> list[Appointment]:
    stmt = (
        select(Appointment)
        .where(Appointment.date == appt_date)
        .order_by(Appointment.time)
    )
    return list(session.execute(stmt).scalars().all())


def get_revenue_summary(session) -> dict:
    """Restituisce un dizionario con revenue di oggi e del mese."""
    today = date.today()
    start_month = today.replace(day=1)

    today_appointments = get_appointments_by_date(session, today)
    today_revenue = sum(a.service.price for a in today_appointments if a.service)

    stmt = (
        select(Appointment, Service)
        .join(Service, Appointment.service_id == Service.id)
        .where(Appointment.date >= start_month)
    )
    month_revenue = sum(
        service.price for _, service in session.execute(stmt).all()
    )

    return {
        "today": today_revenue,
        "month": month_revenue,
        "today_count": len(today_appointments),
    }