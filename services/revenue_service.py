from datetime import date, timedelta
from collections import defaultdict
from sqlalchemy import select, func
from models import Appointment, Service
from services.appointment_service import get_revenue_between, get_appointment_net_revenue


def _get_period_start_date(period: str) -> date:
    """Restituisce la data di inizio del periodo per la selezione incassi."""
    today = date.today()
    if period == "Settimana":
        return today - timedelta(days=6)
    if period == "Mese":
        return today.replace(day=1)
    if period == "Trimestre":
        return today - timedelta(days=89)
    # Anno
    return date(today.year, 1, 1)


def get_revenue_today(session) -> float:
    return get_revenue_between(session, date.today(), date.today())


def get_revenue_month(session) -> float:
    today = date.today()
    start_month = today.replace(day=1)
    return get_revenue_between(session, start_month, today)


def get_daily_revenue(session, days: int = 7) -> list[dict]:
    """Restituisce gli incassi giornalieri per gli ultimi `days` giorni.

    TASK 3: considera solo appuntamenti COMPLETED con pagamento PAID come incassi,
    gestendo i rimborsi (REFUNDED) sottraendo gli importi rimborsati.
    """
    today = date.today()
    start_date = today - timedelta(days=days - 1)

    revenues = {}
    stmt = (
        select(Appointment)
        .where(
            Appointment.date >= start_date,
            Appointment.date <= today,
            Appointment.status == Appointment.STATUS_COMPLETED,
        )
    )
    appointments = list(session.execute(stmt).scalars().all())

    totals = defaultdict(float)
    for appt in appointments:
        totals[appt.date] += get_appointment_net_revenue(appt)

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
    year = today.year
    month = today.month - (months - 1)
    while month <= 0:
        month += 12
        year -= 1
    start_date = date(year, month, 1)

    stmt = (
        select(Appointment)
        .where(
            Appointment.date >= start_date,
            Appointment.date <= today,
            Appointment.status == Appointment.STATUS_COMPLETED,
        )
    )
    appointments = list(session.execute(stmt).scalars().all())

    totals = defaultdict(float)
    for appt in appointments:
        key = (appt.date.year, appt.date.month)
        totals[key] += get_appointment_net_revenue(appt)

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
            "revenue": round(totals.get((cur_y, cur_m), 0.0), 2),
        })
        cur_m += 1
        if cur_m > 12:
            cur_m = 1
            cur_y += 1

    return result


def get_period_revenue_total(session, period: str) -> tuple[float, int]:
    """Restituisce (incasso totale, numero appuntamenti) per il periodo selezionato.

    TASK 3: considera solo appuntamenti COMPLETED con pagamento PAID come incassi.
    """
    today = date.today()
    if period == "Settimana":
        start_date = today - timedelta(days=6)
    elif period == "Mese":
        start_date = today.replace(day=1)
    elif period == "Trimestre":
        start_date = today - timedelta(days=89)
    else:  # Anno
        start_date = today.replace(month=1, day=1)

    total = get_revenue_between(session, start_date, today)

    # Conta gli appuntamenti completati e pagati come servizi effettivamente incassati
    from sqlalchemy import func
    paid_count_result = (
        session.query(func.count(Appointment.id))
        .filter(
            Appointment.date >= start_date,
            Appointment.date <= today,
            Appointment.status == Appointment.STATUS_COMPLETED,
            Appointment.payment_status == Appointment.PAYMENT_PAID,
        )
        .scalar()
    )
    paid_count = paid_count_result if paid_count_result else 0

    return round(float(total), 2), paid_count


def get_top_services(session, period: str = "Mese", limit: int = 5) -> list[dict]:
    """Restituisce i servizi più venduti per il periodo selezionato.

    Conta solo gli appuntamenti COMPLETED con pagamento PAID come servizi venduti.
    """
    today = date.today()
    start_date = _get_period_start_date(period)
    end_date = today

    stmt = (
        select(
            Appointment.service_id.label("service_id"),
            Service.name.label("service_name"),
            func.count(Appointment.id).label("service_count"),
            func.coalesce(func.sum(Appointment.amount_paid), 0.0).label("total_revenue"),
        )
        .join(Service, Appointment.service_id == Service.id)
        .where(
            Appointment.date >= start_date,
            Appointment.date <= end_date,
            Appointment.status == Appointment.STATUS_COMPLETED,
            Appointment.payment_status == Appointment.PAYMENT_PAID,
        )
        .group_by(Appointment.service_id, Service.name)
        .order_by(
            func.count(Appointment.id).desc(),
            func.coalesce(func.sum(Appointment.amount_paid), 0.0).desc(),
        )
        .limit(limit)
    )
    rows = session.execute(stmt).all()
    result = []
    for row in rows:
        result.append({
            "service_id": row[0],
            "service_name": row[1],
            "count": int(row[2]),
            "revenue": round(float(row[3] or 0.0), 2),
        })
    return result


def get_pending_payments(session, period: str = "Mese") -> float:
    """Restituisce gli incassi ancora da registrare per il periodo.

    Considera come "da registrare" gli appuntamenti COMPLETED con pagamento UNPAID.
    """
    today = date.today()
    start_date = _get_period_start_date(period)
    end_date = today

    stmt = (
        select(func.coalesce(func.sum(Appointment.price), 0.0))
        .where(
            Appointment.date >= start_date,
            Appointment.date <= end_date,
            Appointment.status == Appointment.STATUS_COMPLETED,
            Appointment.payment_status == Appointment.PAYMENT_UNPAID,
        )
    )
    total = session.execute(stmt).scalar()
    return round(float(total or 0.0), 2)


def get_refunds(session, period: str = "Mese") -> float:
    """Restituisce i rimborsi per il periodo.

    Somma gli importi pagati (amount_paid) degli appuntamenti COMPLETED con pagamento REFUNDED.
    """
    today = date.today()
    start_date = _get_period_start_date(period)
    end_date = today

    stmt = (
        select(func.coalesce(func.sum(Appointment.amount_paid), 0.0))
        .where(
            Appointment.date >= start_date,
            Appointment.date <= end_date,
            Appointment.status == Appointment.STATUS_COMPLETED,
            Appointment.payment_status == Appointment.PAYMENT_REFUNDED,
        )
    )
    total = session.execute(stmt).scalar()
    return round(float(total or 0.0), 2)
