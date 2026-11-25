from datetime import date, time, timedelta
import pytest
from services.appointment_service import (
    check_appointment_conflict,
    create_appointment,
    delete_appointment,
    get_appointments,
    get_appointments_in_range,
    get_revenue_summary,
    is_collaborator_available,
)
from services.client_service import create_client
from services.collaborator_service import create_collaborator
from services.revenue_service import (
    get_daily_revenue,
    get_monthly_revenue,
    get_period_revenue_total,
    get_revenue_month,
    get_revenue_today,
)
from services.service import create_service


class TestDisponibilitaEAppuntamenti:
    def test_is_collaborator_available_italian_work_days(self, db_session):
        collab = create_collaborator(
            db_session,
            "Mario",
            "Barbiere",
            True,
            time(9, 0),
            time(18, 0),
            ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"],
        )
        monday = date(2025, 1, 6)  # Lunedì
        sunday = date(2025, 1, 12)  # Domenica

        assert is_collaborator_available(db_session, collab.id, monday, time(10, 0)) is True
        assert is_collaborator_available(db_session, collab.id, monday, time(8, 30)) is False
        assert is_collaborator_available(db_session, collab.id, monday, time(18, 30)) is False
        assert is_collaborator_available(db_session, collab.id, sunday, time(10, 0)) is False

    def test_is_collaborator_available_inactive(self, db_session):
        collab = create_collaborator(
            db_session,
            "Anna",
            "Barbiere",
            False,
            time(9, 0),
            time(18, 0),
            ["Lunedì"],
        )
        monday = date(2025, 1, 6)
        assert is_collaborator_available(db_session, collab.id, monday, time(10, 0)) is False

    def test_create_appointment_and_conflict_detection(self, db_session):
        collab = create_collaborator(
            db_session,
            "Mario",
            "Barbiere",
            True,
            time(9, 0),
            time(18, 0),
            ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"],
        )
        service = create_service(db_session, "Taglio", 30, 25.0)
        client1 = create_client(db_session, "Luca", "3334445556")
        client2 = create_client(db_session, "Marco", "3334445557")

        monday = date(2025, 1, 6)
        appt = create_appointment(
            db_session,
            client_id=client1.id,
            service_id=service.id,
            collaborator_id=collab.id,
            appt_date=monday,
            appt_time=time(10, 0),
            notes="Taglio corto",
        )
        assert appt.id is not None

        # Sovrapposizione parziale (10:15 con durata 30 min si sovrappone a 10:00-10:30)
        assert check_appointment_conflict(db_session, collab.id, monday, time(10, 15), 30) is True
        with pytest.raises(ValueError, match="Conflitto di orario"):
            create_appointment(
                db_session,
                client_id=client2.id,
                service_id=service.id,
                collaborator_id=collab.id,
                appt_date=monday,
                appt_time=time(10, 15),
            )

        # Slot adiacente libero (10:30 dopo 10:00-10:30)
        assert check_appointment_conflict(db_session, collab.id, monday, time(10, 30), 30) is False
        appt2 = create_appointment(
            db_session,
            client_id=client2.id,
            service_id=service.id,
            collaborator_id=collab.id,
            appt_date=monday,
            appt_time=time(10, 30),
        )
        assert appt2.id is not None

        # Giorno non lavorativo (Domenica)
        sunday = date(2025, 1, 12)
        with pytest.raises(ValueError, match="Collaboratore non disponibile"):
            create_appointment(
                db_session,
                client_id=client1.id,
                service_id=service.id,
                collaborator_id=collab.id,
                appt_date=sunday,
                appt_time=time(10, 0),
            )

    def test_get_range_and_delete_appointment(self, db_session):
        collab = create_collaborator(
            db_session,
            "Mario",
            "Barbiere",
            True,
            time(9, 0),
            time(18, 0),
            ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"],
        )
        service = create_service(db_session, "Barba", 20, 15.0)
        client = create_client(db_session, "Luca", "3334445556")

        d1 = date(2025, 1, 6)
        d2 = d1 + timedelta(days=2)
        a1 = create_appointment(db_session, client.id, service.id, collab.id, d1, time(9, 0))
        create_appointment(db_session, client.id, service.id, collab.id, d2, time(11, 0))

        assert len(get_appointments(db_session, date_filter=d1)) == 1
        assert len(get_appointments_in_range(db_session, d1, d2)) == 2
        assert delete_appointment(db_session, a1.id) is True
        assert len(get_appointments_in_range(db_session, d1, d2)) == 1


class TestIncassi:
    def test_revenue_calculations(self, db_session):
        collab = create_collaborator(
            db_session,
            "Mario",
            "Barbiere",
            True,
            time(8, 0),
            time(20, 0),
            ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"],
        )
        s1 = create_service(db_session, "Taglio", 30, 20.0)
        s2 = create_service(db_session, "Barba", 20, 12.5)
        client = create_client(db_session, "Cliente Test", "333000111")

        today = date.today()
        create_appointment(db_session, client.id, s1.id, collab.id, today, time(10, 0))
        create_appointment(db_session, client.id, s2.id, collab.id, today, time(11, 0))

        summary = get_revenue_summary(db_session)
        assert summary["today"] == 32.5
        assert summary["month"] >= 32.5
        assert summary["today_count"] == 2
        assert get_revenue_today(db_session) == 32.5
        assert get_revenue_month(db_session) >= 32.5

        daily = get_daily_revenue(db_session, days=7)
        assert len(daily) == 7
        assert daily[-1]["date"] == today
        assert daily[-1]["revenue"] == 32.5

        monthly = get_monthly_revenue(db_session, months=6)
        assert len(monthly) == 6
        assert monthly[-1]["revenue"] >= 32.5

        total_week, count_week = get_period_revenue_total(db_session, "Settimana")
        assert total_week == 32.5
        assert count_week == 2
