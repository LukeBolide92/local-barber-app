from database import get_session
from services.appointment_service import get_revenue_summary


def get_revenue_today(session) -> float:
    return get_revenue_summary(session)["today"]


def get_revenue_month(session) -> float:
    return get_revenue_summary(session)["month"]