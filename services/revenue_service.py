from datetime import date, timedelta
from collections import defaultdict
from sqlalchemy import select
from models import Appointment, Service
from services.appointment_service import get_revenue_summary


def get_revenue_today(session) -> float:
    return get_revenue_summary(session)["today"]


def get_revenue_month(session) -> float:
    return get_revenue_summary(session)["month"]


def get_daily_revenue(session, days: int = 7) -> list[dict]:
    """Restituisce gli incassi giornalieri per gli ultimi `days` giorni."""
    today = date.today()
    start_date = today - timedelta(days=days - 1)

    stmt = (
        select(Appointment.date, Service.price)
        .join(Service, Appointment.service_id == Service.id)
        .where(Appointment.date >= start_date, Appointment.date <= today)
    )
    totals = defaultdict(float)
    for appt_date, price in session.execute(stmt).all():
        totals[appt_date] += float(price)

    return [
        {
            "date": start_date + timedelta(days=i),
            "revenue": round(totals[start_date + timedelta(days=i)], 2),
        }
        for i in range(days)
    ]


def get_monthly_revenue(session, months: int = 12) -> list[dict]:
    """Restituisce gli incassi aggregati per mese dal database."""
    today = date.today()
    # Calculate start month roughly `months - 1` months back
    year = today.year
    month = today.month - (months - 1)
    while month <= 0:
        month += 12
        year -= 1
    start_date = date(year, month, 1)

    stmt = (
        select(Appointment.date, Service.price)
        .join(Service, Appointment.service_id == Service.id)
        .where(Appointment.date >= start_date, Appointment.date <= today)
    )
    totals = defaultdict(float)
    for appt_date, price in session.execute(stmt).all():
        key = (appt_date.year, appt_date.month)
        totals[key] += float(price)

    month_names = [
        "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre",
    ]

    result = []
    cur_y, cur_m = year, month
    for _ in range(months):
        label = f"{month_names[cur_m - 1]} {cur_y}"
        result.append({
            "month": label,
            "revenue": round(totals[(cur_y, cur_m)], 2),
        })
        cur_m += 1
        if cur_m > 12:
            cur_m = 1
            cur_y += 1

    return result


def get_period_revenue_total(session, period: str) -> tuple[float, int]:
    """Restituisce (incasso totale, numero appuntamenti) per il periodo selezionato."""
    today = date.today()
    if period == "Settimana":
        start_date = today - timedelta(days=6)
    elif period == "Mese":
        start_date = today.replace(day=1)
    elif period == "Trimestre":
        start_date = today - timedelta(days=89)
    else:  # Anno
        start_date = today.replace(month=1, day=1)

    stmt = (
        select(Service.price)
        .select_from(Appointment)
        .join(Service, Appointment.service_id == Service.id)
        .where(Appointment.date >= start_date, Appointment.date <= today)
    )
    prices = [float(row[0]) for row in session.execute(stmt).all()]
    return round(sum(prices), 2), len(prices)
