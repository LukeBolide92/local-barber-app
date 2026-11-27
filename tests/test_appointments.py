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
    complete_appointment,
    cancel_appointment,
    register_no_show,
    update_appointment,
)
from services.payment_service import (
    register_payment,
    register_refund,
    get_payment_details,
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
        appt1 = create_appointment(db_session, client.id, s1.id, collab.id, today, time(10, 0))
        appt2 = create_appointment(db_session, client.id, s2.id, collab.id, today, time(11, 0))
        # Completa gli appuntamenti
        complete_appointment(db_session, appt1.id)
        complete_appointment(db_session, appt2.id)
        # Registra i pagamenti dopo il completamento
        register_payment(db_session, appt1.id, amount=s1.price, method="Contanti")
        register_payment(db_session, appt2.id, amount=s2.price, method="Carta")

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


class TestPagamenti:
    def test_register_payment_only_after_completed(self, db_session):
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
        client = create_client(db_session, "Cliente Test", "333000111")

        today = date.today()
        appt = create_appointment(db_session, client.id, s1.id, collab.id, today, time(10, 0))

        # Pagamento non consentito per appuntamento BOOKED
        from services.appointment_service import get_appointment_by_id
        with pytest.raises(ValueError, match="stato"):
            register_payment(db_session, appt.id, amount=20.0, method="Contanti")

        # Completa e registra pagamento
        complete_appointment(db_session, appt.id)
        paid_appt = register_payment(db_session, appt.id, amount=20.0, method="Contanti")
        assert paid_appt.payment_status == "PAID"
        assert paid_appt.amount_paid == 20.0
        assert paid_appt.payment_method == "Contanti"

        details = get_payment_details(db_session, appt.id)
        assert details["payment_status"] == "PAID"
        assert details["amount_paid"] == 20.0

    def test_complete_appointment_auto_sets_paid(self, db_session):
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
        client = create_client(db_session, "Cliente Test", "333000111")

        today = date.today()
        appt = create_appointment(db_session, client.id, s1.id, collab.id, today, time(10, 0))
        assert appt.payment_status == "UNPAID"

        completed = complete_appointment(db_session, appt.id, recorded_price=20.0)
        assert completed.status == "COMPLETED"
        # Completamento -> automaticamente PAID
        assert completed.payment_status == "PAID"
        assert completed.amount_paid == 20.0
        assert completed.payment_method == "Contanti"

    def test_status_change_to_non_completed_resets_unpaid(self, db_session):
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
        client = create_client(db_session, "Cliente Test", "333000111")

        today = date.today()
        appt = create_appointment(db_session, client.id, s1.id, collab.id, today, time(10, 0))
        complete_appointment(db_session, appt.id, recorded_price=20.0)
        assert appt.payment_status == "PAID"

        # Cambio stato in CANCELLED -> pagamento torna a UNPAID
        updated = update_appointment(db_session, appt.id, status="CANCELLED")
        assert updated.status == "CANCELLED"
        assert updated.payment_status == "UNPAID"
        assert updated.amount_paid == 0.0

        # Cambio stato in BOOKED -> pagamento torna a UNPAID
        updated2 = update_appointment(db_session, appt.id, status="BOOKED")
        assert updated2.status == "BOOKED"
        assert updated2.payment_status == "UNPAID"

    def test_refund_only_after_completed(self, db_session):
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
        client = create_client(db_session, "Cliente Test", "333000111")

        today = date.today()
        appt = create_appointment(db_session, client.id, s1.id, collab.id, today, time(10, 0))
        complete_appointment(db_session, appt.id)
        register_payment(db_session, appt.id, amount=20.0, method="Contanti")

        refunded = register_refund(db_session, appt.id)
        assert refunded.payment_status == "REFUNDED"

        # Dopo il rimborso l'incasso netto torna a zero
        summary = get_revenue_summary(db_session)
        assert summary["today"] == 0.0
        assert get_revenue_today(db_session) == 0.0
        daily = get_daily_revenue(db_session, days=7)
        assert daily[-1]["revenue"] == 0.0
