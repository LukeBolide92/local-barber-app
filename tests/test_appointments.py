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
    complete_appointment_and_register_quick_payment,
)
from services.client_service import create_client
from services.collaborator_service import create_collaborator
from services.revenue_service import (
    get_daily_revenue,
    get_monthly_revenue,
    get_period_revenue_total,
    get_revenue_month,
    get_revenue_today,
    get_top_services,
    get_pending_payments,
    get_refunds,
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

    def test_is_collaborator_available_full_interval_within_working_hours(self, db_session):
        """TASK 4: l'intero intervallo dell'appuntamento deve rientrare nel turno lavorativo."""
        collab = create_collaborator(
            db_session,
            "Mario",
            "Barbiere",
            True,
            time(9, 0),
            time(19, 0),
            ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"],
        )

        # Appuntamento che termina esattamente alla chiusura -> DISPONIBILE
        assert is_collaborator_available(db_session, collab.id, date(2025, 1, 6), time(18, 0), duration_minutes=60) is True
        # Appuntamento che supera la chiusura -> NON DISPONIBILE
        assert is_collaborator_available(db_session, collab.id, date(2025, 1, 6), time(18, 45), duration_minutes=45) is False
        # Appuntamento che inizia prima dell'orario di apertura -> NON DISPONIBILE
        assert is_collaborator_available(db_session, collab.id, date(2025, 1, 6), time(8, 30), duration_minutes=30) is False

    def test_is_collaborator_available_conflict_full_interval(self, db_session):
        """TASK 4: sovrapposizioni -> NON disponibile; appuntamenti consecutivi -> disponibile."""
        collab = create_collaborator(
            db_session,
            "Mario",
            "Barbiere",
            True,
            time(9, 0),
            time(19, 0),
            ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"],
        )
        service = create_service(db_session, "Taglio", 30, 25.0)
        client = create_client(db_session, "Luca", "3334445556")
        monday = date(2025, 1, 6)
        appt = create_appointment(db_session, client.id, service.id, collab.id, monday, time(10, 0))

        # Sovrapposizione (10:15 + 30 min -> 10:45 > inizio 10:00) -> NON DISPONIBILE
        assert is_collaborator_available(db_session, collab.id, monday, time(10, 15), duration_minutes=30) is False
        # Convenzionale (10:30 inizia quando il precedente termina) -> DISPONIBILE
        assert is_collaborator_available(db_session, collab.id, monday, time(10, 30), duration_minutes=30) is True

    def test_is_collaborator_available_excludes_cancelled(self, db_session):
        """TASK 4: gli appuntamenti annullati non bloccano la disponibilità."""
        collab = create_collaborator(
            db_session,
            "Mario",
            "Barbiere",
            True,
            time(9, 0),
            time(19, 0),
            ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"],
        )
        service = create_service(db_session, "Taglio", 30, 25.0)
        client = create_client(db_session, "Luca", "3334445556")
        monday = date(2025, 1, 6)
        appt = create_appointment(db_session, client.id, service.id, collab.id, monday, time(10, 0))
        assert is_collaborator_available(db_session, collab.id, monday, time(10, 15), duration_minutes=30) is False
        cancel_appointment(db_session, appt.id)
        assert is_collaborator_available(db_session, collab.id, monday, time(10, 15), duration_minutes=30) is True

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

    def test_complete_then_register_payment(self, db_session):
        """TASK 2: completamento senza pagamento automatico + registrazione successiva del pagamento."""
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
        completed = complete_appointment(db_session, appt.id, recorded_price=20.0)
        assert completed.status == "COMPLETED"
        assert completed.payment_status == "UNPAID"

        # Pagamento successivo al completamento
        paid = register_payment(db_session, appt.id, amount=20.0, method="Contanti")
        assert paid.payment_status == "PAID"
        assert paid.amount_paid == 20.0

    def test_register_payment_rejected_for_uncompleted_appointment(self, db_session):
        """TASK 2: il pagamento è consentito solo per appuntamenti COMPLETED."""
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
        with pytest.raises(ValueError, match="stato"):
            register_payment(db_session, appt.id, amount=20.0, method="Contanti")

    def test_double_payment_rejected(self, db_session):
        """TASK 2: non è possibile registrare due pagamenti per lo stesso appuntamento."""
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
        with pytest.raises(ValueError, match="già"):
            register_payment(db_session, appt.id, amount=20.0, method="Contanti")

    def test_register_payment_rejected_after_refund(self, db_session):
        """TASK 2: non è possibile registrare un pagamento per un appuntamento rimborsato."""
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
        register_refund(db_session, appt.id)
        with pytest.raises(ValueError, match="rimborsato"):
            register_payment(db_session, appt.id, amount=20.0, method="Contanti")

    def test_quick_complete_and_register_payment(self, db_session):
        """TASK 2: operazione rapida completa + registra contestivamente il pagamento in contanti."""
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
        result = complete_appointment_and_register_quick_payment(
            db_session, appt.id, amount=20.0, method="Contanti"
        )
        assert result is not None
        assert result.status == "COMPLETED"
        assert result.payment_status == "PAID"
        assert result.amount_paid == 20.0
        assert result.payment_method == "Contanti"

    def test_complete_appointment_does_not_register_payment(self, db_session):
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
        # TASK 2: il completamento non registra automaticamente il pagamento
        assert completed.payment_status == "UNPAID"
        assert completed.amount_paid is None

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
        assert appt.payment_status == "UNPAID"

        # Cambio stato in CANCELLED -> pagamento torna a UNPAID
        updated = update_appointment(db_session, appt.id, status="CANCELLED")
        assert updated.status == "CANCELLED"
        assert updated.payment_status == "UNPAID"
        assert updated.amount_paid == 0.0

        # Cambio stato in BOOKED -> pagamento torna a UNPAID
        updated2 = update_appointment(db_session, appt.id, status="BOOKED")
        assert updated2.status == "BOOKED"
        assert updated2.payment_status == "UNPAID"

    def test_update_paid_appointment_status_change_rejected(self, db_session):
        """TASK 3 (FASE 4.2): non si può modificare lo stato di un appuntamento pagato."""
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

        # Un appuntamento pagato non può essere riportato a uno stato incompleto
        with pytest.raises(ValueError, match="pagato"):
            update_appointment(db_session, appt.id, status="CANCELLED")

    def test_update_paid_appointment_preserves_payment_status(self, db_session):
        """TASK 3 (FASE 4.2): modifica ordinaria di un appuntamento pagato -> pagamento invariato."""
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

        updated = update_appointment(db_session, appt.id, notes="Cliente richiede ritocco")
        assert updated.payment_status == "PAID"
        assert updated.amount_paid == 20.0

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

    def test_refund_blocked_for_unpaid_appointment(self, db_session):
        """TASK 3: il rimborso è consentito solo per appuntamenti effettivamente pagati."""
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
        # Appuntamento completato ma non pagato -> rimborso non consentito
        with pytest.raises(ValueError, match="pagato"):
            register_refund(db_session, appt.id)

    def test_double_refund_blocked(self, db_session):
        """TASK 3: non è possibile rimborsare due volte lo stesso pagamento."""
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
        with pytest.raises(ValueError, match="già"):
            register_refund(db_session, appt.id)

    def test_refund_amount_not_exceeding_paid_blocked(self, db_session):
        """TASK 3: non è possibile rimborsare un importo superiore a quello incassato."""
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
        with pytest.raises(ValueError, match="superiore"):
            register_refund(db_session, appt.id, amount=25.0)

    def test_refund_partial_not_allowed(self, db_session):
        """TASK 2 (FASE 4.2): per questa versione supportiamo esclusivamente rimborsi totali."""
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

        # Un rimborso parziale (es. 10 di 20) deve essere rifiutato
        with pytest.raises(ValueError, match="parziale"):
            register_refund(db_session, appt.id, amount=10.0)

    def test_refund_with_full_amount_allowed(self, db_session):
        """TASK 2 (FASE 4.2): rimborso esplicito dell'intero importo va accettato."""
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

        refunded = register_refund(db_session, appt.id, amount=20.0)
        assert refunded.payment_status == "REFUNDED"
        assert get_refunds(db_session, period="Mese") == 20.0


class TestIncassiAggiuntivi:
    def test_top_services_returns_highest_count(self, db_session):
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
        # Taglio: 2 servizi completati e pagati; Barba: 1 servizio completato e pagato
        appt1 = create_appointment(db_session, client.id, s1.id, collab.id, today, time(10, 0))
        appt2 = create_appointment(db_session, client.id, s1.id, collab.id, today, time(11, 0))
        appt3 = create_appointment(db_session, client.id, s2.id, collab.id, today, time(12, 0))
        complete_appointment(db_session, appt1.id)
        complete_appointment(db_session, appt2.id)
        complete_appointment(db_session, appt3.id)
        register_payment(db_session, appt1.id, amount=20.0, method="Contanti")
        register_payment(db_session, appt2.id, amount=20.0, method="Contanti")
        register_payment(db_session, appt3.id, amount=12.5, method="Carta")

        top = get_top_services(db_session, period="Mese", limit=5)
        assert len(top) == 2
        # Taglio è il servizio più venduto (2 servizi)
        assert top[0]["service_name"] == "Taglio"
        assert top[0]["count"] == 2
        assert top[0]["revenue"] == 40.0
        # Barba è secondo (1 servizio)
        assert top[1]["service_name"] == "Barba"
        assert top[1]["count"] == 1
        assert top[1]["revenue"] == 12.5

    def test_get_pending_payments_only_unpaid_completed(self, db_session):
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
        appt1 = create_appointment(db_session, client.id, s1.id, collab.id, today, time(10, 0))
        appt2 = create_appointment(db_session, client.id, s1.id, collab.id, today, time(11, 0))
        # Completa -> l'auto-PAID imposta il pagamento
        complete_appointment(db_session, appt1.id)
        complete_appointment(db_session, appt2.id)
        # Simula un pagamento completato ma non ancora registrato (UNPAID)
        appt1.payment_status = "UNPAID"
        appt2.payment_status = "UNPAID"
        pending = get_pending_payments(db_session, period="Mese")
        # 2 appuntamenti completati senza pagamento registrato
        assert pending == 40.0

    def test_get_refunds_returns_refund_amount(self, db_session):
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
        assert get_refunds(db_session, period="Mese") == 0.0

        register_refund(db_session, appt.id)
        assert get_refunds(db_session, period="Mese") == 20.0
