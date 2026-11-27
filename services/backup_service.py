from contextlib import closing
from datetime import datetime
from pathlib import Path
import sqlite3
from db.database import DB_PATH, engine

DEFAULT_BACKUP_DIR = Path("backups")
REQUIRED_TABLES = {"clients", "services", "collaborators", "appointments"}
SQLITE_HEADER = b"SQLite format 3\x00"


def ensure_backup_dir(backup_dir: str | Path = DEFAULT_BACKUP_DIR) -> Path:
    path = Path(backup_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_backup(
    db_path: str | Path = DB_PATH,
    backup_dir: str | Path = DEFAULT_BACKUP_DIR,
    prefix: str = "barber_backup",
) -> Path:
    """Crea una copia di backup consistente del database SQLite."""
    src_path = Path(db_path)
    if not src_path.exists():
        raise FileNotFoundError(f"Database non trovato: {src_path}")

    dest_dir = ensure_backup_dir(backup_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_path = dest_dir / f"{prefix}_{timestamp}.db"
    counter = 1
    while dest_path.exists():
        dest_path = dest_dir / f"{prefix}_{timestamp}_{counter}.db"
        counter += 1

    with closing(sqlite3.connect(str(src_path))) as src_conn:
        with closing(sqlite3.connect(str(dest_path))) as dst_conn:
            src_conn.backup(dst_conn)

    return dest_path


def list_backups(backup_dir: str | Path = DEFAULT_BACKUP_DIR) -> list[dict]:
    """Restituisce l'elenco dei file di backup ordinati dal più recente."""
    dir_path = Path(backup_dir)
    if not dir_path.exists():
        return []

    files = [p for p in dir_path.iterdir() if p.is_file() and p.suffix.lower() == ".db"]
    files.sort(key=lambda p: (p.stat().st_mtime, p.name), reverse=True)

    return [
        {
            "filename": p.name,
            "path": p,
            "size_kb": round(p.stat().st_size / 1024, 2),
            "created_at": datetime.fromtimestamp(p.stat().st_mtime),
        }
        for p in files
    ]


def validate_backup_file(backup_path: str | Path) -> None:
    """Verifica che il file sia un database SQLite valido con le tabelle richieste."""
    path = Path(backup_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"File di backup non trovato: {path}")

    if path.stat().st_size < len(SQLITE_HEADER):
        raise ValueError("Il file selezionato non è un database SQLite valido.")

    with path.open("rb") as f:
        header = f.read(len(SQLITE_HEADER))
    if header != SQLITE_HEADER:
        raise ValueError("Il file selezionato non è un database SQLite valido.")

    try:
        with closing(sqlite3.connect(str(path))) as conn:
            integrity = conn.execute("PRAGMA integrity_check;").fetchone()
            if not integrity or integrity[0] != "ok":
                raise ValueError("Il file di backup risulta danneggiato.")

            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table';"
                ).fetchall()
            }
    except sqlite3.DatabaseError as exc:
        raise ValueError(f"Impossibile leggere il database di backup: {exc}") from exc

    missing = REQUIRED_TABLES - tables
    if missing:
        raise ValueError(
            f"Il backup non contiene tutte le tabelle necessarie ({', '.join(sorted(missing))})."
        )


def restore_backup(
    backup_path: str | Path,
    db_path: str | Path = DB_PATH,
    create_safety_backup: bool = True,
    backup_dir: str | Path = DEFAULT_BACKUP_DIR,
) -> Path | None:
    """Ripristina il database da un file di backup validato."""
    src_path = Path(backup_path)
    validate_backup_file(src_path)

    dst_path = Path(db_path)
    safety_backup_path = None
    if create_safety_backup and dst_path.exists():
        safety_backup_path = create_backup(
            db_path=dst_path,
            backup_dir=backup_dir,
            prefix="barber_pre_restore",
        )

    if dst_path.resolve() == Path(DB_PATH).resolve():
        engine.dispose()

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(str(src_path))) as src_conn:
        with closing(sqlite3.connect(str(dst_path))) as dst_conn:
            src_conn.backup(dst_conn)

    if dst_path.resolve() == Path(DB_PATH).resolve():
        engine.dispose()

    return safety_backup_path


def delete_backup(backup_path: str | Path) -> bool:
    """Elimina un file di backup esistente."""
    path = Path(backup_path)
    if not path.exists() or not path.is_file():
        return False
    path.unlink()
    return True
