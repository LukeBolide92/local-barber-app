from datetime import time
import pytest
from services.client_service import (
    create_client,
    delete_client,
    get_client_by_id,
    get_clients,
    search_clients,
    update_client,
)
from services.collaborator_service import (
    create_collaborator,
    delete_collaborator,
    deserialize_work_days,
    get_collaborators,
    update_collaborator,
)
from services.service import (
    create_service,
    delete_service,
    get_services,
    update_service,
)


class TestClienti:
    def test_create_and_get_client(self, db_session):
        c = create_client(db_session, "  Mario Rossi ", " 3331234567 ", " mario@test.it ")
        assert c.id is not None
        assert c.name == "Mario Rossi"
        assert c.phone == "3331234567"
        assert c.email == "mario@test.it"

        clients = get_clients(db_session)
        assert len(clients) == 1
        assert get_client_by_id(db_session, c.id).name == "Mario Rossi"

    def test_create_client_unique_name_case_insensitive(self, db_session):
        create_client(db_session, "Mario Rossi", "3334445556")
        with pytest.raises(ValueError, match="Esiste già un cliente con nome"):
            create_client(db_session, "  mario rossi ", "3334445557")

    def test_update_client_uniqueness(self, db_session):
        c1 = create_client(db_session, "Mario Rossi", "3334445556")
        create_client(db_session, "Luca Bianchi", "3334445558")

        # Aggiornare lo stesso cliente mantenendo il proprio nome è permesso
        updated = update_client(db_session, c1.id, "Mario Rossi", "3339999999", None)
        assert updated.phone == "3339999999"

        # Aggiornare al nome di un altro cliente esistente deve fallire
        with pytest.raises(ValueError, match="Esiste già un cliente con nome"):
            update_client(db_session, c1.id, "luca bianchi", "3339999999")

    def test_search_and_delete_client(self, db_session):
        c1 = create_client(db_session, "Mario Rossi", "333111222", "mario@example.com")
        create_client(db_session, "Luigi Verdi", "333999888", None)

        assert len(search_clients(db_session, "mario")) == 1
        assert len(search_clients(db_session, "999888")) == 1
        assert len(search_clients(db_session, "")) == 2

        assert delete_client(db_session, c1.id) is True
        assert delete_client(db_session, 9999) is False


class TestServizi:
    def test_create_service_unique_name(self, db_session):
        s1 = create_service(db_session, "Taglio uomo", 30, 25.0)
        assert s1.id is not None
        with pytest.raises(ValueError, match="Esiste già un servizio con nome"):
            create_service(db_session, "taglio uomo", 40, 30.0)

    def test_update_and_delete_service(self, db_session):
        s1 = create_service(db_session, "Taglio", 30, 20.0)
        create_service(db_session, "Barba", 20, 15.0)

        with pytest.raises(ValueError, match="Esiste già un servizio con nome"):
            update_service(db_session, s1.id, "BARBA", 30, 20.0)

        updated = update_service(db_session, s1.id, "Taglio Completo", 45, 28.0)
        assert updated.name == "Taglio Completo"
        assert updated.duration_minutes == 45
        assert updated.price == 28.0
        assert len(get_services(db_session)) == 2

        assert delete_service(db_session, s1.id) is True
        assert len(get_services(db_session)) == 1


class TestCollaboratori:
    def test_create_collaborator_unique_name(self, db_session):
        c1 = create_collaborator(
            db_session,
            "Luca Bianchi",
            "Barbiere",
            True,
            time(9, 0),
            time(18, 0),
            ["Lunedì", "Martedì"],
        )
        assert c1.id is not None
        assert deserialize_work_days(c1.work_days) == ["Lunedì", "Martedì"]

        with pytest.raises(ValueError, match="Esiste già un collaboratore con nome"):
            create_collaborator(
                db_session,
                "LUCA BIANCHI",
                "Barbiere",
                True,
                time(9, 0),
                time(18, 0),
                ["Lunedì"],
            )

    def test_update_filter_and_delete_collaborator(self, db_session):
        c1 = create_collaborator(db_session, "Marco", "Barbiere", True)
        c2 = create_collaborator(db_session, "Paolo", "Apprendista", False)

        assert len(get_collaborators(db_session)) == 2
        assert [c.name for c in get_collaborators(db_session, only_available=True)] == ["Marco"]

        with pytest.raises(ValueError, match="Esiste già un collaboratore con nome"):
            update_collaborator(
                db_session,
                c1.id,
                "Paolo",
                "Barbiere",
                True,
                time(9, 0),
                time(18, 0),
                ["Lunedì"],
            )

        updated = update_collaborator(
            db_session,
            c2.id,
            "Paolo Rossi",
            "Barbiere capo",
            True,
            time(8, 30),
            time(19, 0),
            ["Martedì", "Mercoledì"],
        )
        assert updated.name == "Paolo Rossi"
        assert updated.availability == 1
        assert delete_collaborator(db_session, c1.id) is True
