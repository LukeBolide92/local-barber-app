from datetime import time
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.backup_service import (
    create_backup,
    delete_backup,
    list_backups,
    restore_backup,
    validate_backup_file,
)
from services.client_service import create_client, get_clients


class TestBackupService:
    def test_create_list_and_delete_backup(self, db_session, db_path, tmp_path):
        create_client(db_session, "Mario Rossi", "333123456")
        backup_dir = tmp_path / "backups"

        backup_file = create_backup(db_path=db_path, backup_dir=backup_dir)
        assert backup_file.exists()
        assert backup_file.suffix == ".db"

        backups = list_backups(backup_dir=backup_dir)
        assert len(backups) == 1
        assert backups[0]["filename"] == backup_file.name
        assert backups[0]["size_kb"] > 0

        assert delete_backup(backup_file) is True
        assert list_backups(backup_dir=backup_dir) == []
        assert delete_backup(backup_file) is False

    def test_create_backup_missing_db_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            create_backup(db_path=tmp_path / "non_existent.db", backup_dir=tmp_path / "backups")

    def test_validate_backup_rejects_invalid_file(self, tmp_path):
        bad_file = tmp_path / "not_a_db.db"
        bad_file.write_text("questo non è sqlite", encoding="utf-8")

        with pytest.raises(ValueError, match="database SQLite valido"):
            validate_backup_file(bad_file)

    def test_restore_backup_restores_previous_state(self, db_session, db_path, tmp_path):
        create_client(db_session, "Mario Rossi", "333123456")
        backup_dir = tmp_path / "backups"

        # Backup con 1 cliente
        backup_file = create_backup(db_path=db_path, backup_dir=backup_dir)

        # Aggiungiamo un secondo cliente dopo il backup
        create_client(db_session, "Luca Bianchi", "333987654")
        assert len(get_clients(db_session)) == 2

        # Chiudiamo la sessione prima del ripristino
        db_session.close()

        safety_path = restore_backup(
            backup_path=backup_file,
            db_path=db_path,
            create_safety_backup=True,
            backup_dir=backup_dir,
        )
        assert safety_path is not None
        assert safety_path.exists()
        assert "barber_pre_restore_" in safety_path.name

        # Verifichiamo su una nuova sessione che sia tornato a 1 solo cliente
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Session = sessionmaker(bind=engine, expire_on_commit=False)
        try:
            with Session() as new_session:
                clients = get_clients(new_session)
                assert [c.name for c in clients] == ["Mario Rossi"]
        finally:
            engine.dispose()
