# FASE 1 – REPORT: ANALISI ARCHITETTURALE

> Data: 2025-11-27 · Progetto: Local Barber Manager (`local-barber-app`) · Feature: `prompt-supabase.md`

---

## 1. Stack e struttura livelli

- **Entry point**: `app.py` → `main.py` (wrapper `streamlit run app.py`) → `st.navigation` con 7 pages in `pages/`.
- **Livello UI**: `pages/1_Dashboard.py` … `pages/7_Impostazioni.py`. Nessun accesso diretto al DB da UI; tutti i dati passano dai service.
- **Livello servizi**: `services/` (client, service, collaborator, appointment, payment, revenue, backup). `services/__init__.py` è vuoto: gli import sono per modulo (`from services.client_service import ...`).
- **Livello modelli**: `models/` (`Client`, `Service`, `Collaborator`, `Appointment`) — SQLAlchemy 2.0 style (`Mapped`/`mapped_column`), `DeclarativeBase` da `db.database.Base`.
- **Livello dati**: `db/database.py` (engine SQLite, sessioni, init/migrazioni).
- **Utilità**: `utils/page_header.py`.

## 2. Modelli SQLAlchemy e tabelle attualmente utilizzate (4 tabelle)

| Tabella | Colonne principali | Note |
|---|---|---|
| `clients` | `id` PK, `name` VARCHAR(100) NN, `phone` VARCHAR(20) NN, `email` VARCHAR(120) NULL | 1:N → appointments |
| `services` | `id` PK, `name` VARCHAR(100) NN, `duration_minutes` INT NN, `price` FLOAT NN | 1:N → appointments |
| `collaborators` | `id` PK, `name`, `role`, `availability` INT (1/0), `start_time` TIME NN, `end_time` TIME NN, `work_days` VARCHAR NULL (JSON) | 1:N → appointments |
| `appointments` | `id` PK, `client_id` FK→clients, `service_id` FK→services, `collaborator_id` FK→collaborators, `date` DATE, `time` TIME, `notes` VARCHAR(255) NULL, `status` VARCHAR(20) DEFAULT 'BOOKED', `price` FLOAT NULL, `duration_minutes` INT NULL, **payment**: `payment_status` TEXT DEFAULT 'UNPAID', `amount_paid` REAL, `payment_datetime` DATETIME, `payment_method` TEXT | Stati: BOOKED/COMPLETED/CANCELLED/NO_SHOW; Pagamenti: UNPAID/PAID/REFUNDED |

**Relazioni**: tutte le FK sono `NOT NULL` e referenziano le PK delle rispettive tabelle. Nessun indice esplicito oltre le PK (in SQLite le FK non creano indici di supporto automatici; in PostgreSQL ne creano uno automatico sulle colonne non-PK).

## 3. Inizializzazione e migrazioni DB

- Attuale meccanismo: `init_db()` → `Base.metadata.create_all(engine)` + `_add_payment_columns_if_missing(engine, session_factory)`.
- La migrazione pagamenti è **manuale/custom**: aggiunge solo le colonne mancanti via `ALTER TABLE … ADD COLUMN` e fa backfill dei dati esistenti (COMPLETED→PAID, altri→UNPAID).
- **Nessun Alembic** né sistema di migrazioni versionate al momento → la Fase 8 del piano sarà quella da introdurre.

## 4. Gestione transazioni/sessioni

- `get_session()` context manager (commit/rollback + logging) e `get_db_session()` (sessione da chiudere manualmente).
- **Pattern consolidato**: i service accettano `session` come parametro (funzioni pure rispetto alla sessione) → pattern già predisposto per separare la logica dal DB engine.

## 5. Servizi esistenti (tutti operano su `session`)

- `appointment_service.py` (conflitti, disponibilità, CRUD, revenue per appuntamento)
- `payment_service.py` (register_payment, refund, completamento+pago atomico, quick payment)
- `client_service.py`, `service.py`, `collaborator_service.py`, `revenue_service.py`, `backup_service.py` (usa **sqlite3** backup API, non SQLAlchemy)

## 6. Punti critici già emersi per il futuro collegamento Supabase

1. **Solo SQLite oggi**: ogni layer (engine, backup, migrazioni) è SQLite-specifico → per Supabase serve un'engine PostgreSQL (es. `psycopg2`) condivisa.
2. **Struttura tabellare pensata per il porto**: nomi tabelle lowercase plural, PK int, FKs — coerente con PostgreSQL.
3. **Tipi data**: `Date`/`Time`/`DateTime` SQLAlchemy vs PostgreSQL; `work_days` come VARCHAR JSON vs tipo JSON nativo PG.
4. **Pagamento**: oggi integrato come colonne su `appointments` (nessuna tabella pagamenti separata).
5. **Nessuna credenziale o configurazione DB attualmente presente** nel codice (tutto via env `BARBER_DB_PATH`).

## 7. Test attuali

- `pytest` con fixture `db_session`/`db_path` (SQLite temp via `tmp_path`) in `tests/conftest.py`.
- Copertura: appuntamenti, backup, migrazioni pagamenti, demo, transazioni.

---

## Stato della Fase 1

✅ **Analisi architetturale completata**. Nessun codice stato modificato (tranne file `.pyc` di cache, non versionati).

**Prossima fase prevista: Fase 2 – Verifica Management API**.

---

## Report finale della Fase 1 (da richiamare nelle conversazioni successive)

- **Architettura attuale**: Streamlit UI → service layer (funzioni che accettano `session`) → SQLAlchemy models → SQLite (`db/database.py`).
- **File toccati in questa fase**: `doc/fase-1-analisi-architetturale.md` (creato in fase di report).
- **Endpoint Management API**: non ancora analizzati (Fase 2).
- **Struttura database rilevata**: 4 tabelle (`clients`, `services`, `collaborators`, `appointments`) con FK e stati pagamenti incorporati nelle colonne dell'appuntamento.
- **Migrazioni**: nessun sistema versionato (Alembic assente) → da introdurre in Fase 8.
- **Gestione transazioni**: pattern `get_session()` context manager consolidato.
