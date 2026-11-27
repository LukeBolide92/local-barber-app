# Barber Manager

Gestionale locale semplice e completo per barbieri, sviluppato in Python con **Streamlit**, **SQLite** e **SQLAlchemy 2**.  
Progettato per funzionare interamente in locale su PC Windows senza servizi cloud o dipendenze esterne.

---

## Funzionalità principali

- **Dashboard (`pages/1_Dashboard.py`)**: riepilogo degli appuntamenti di oggi, numero appuntamenti e incassi giornalieri/mensili.
- **Appuntamenti (`pages/2_Appuntamenti.py`)**:
  - Elenco filtrabile per data, collaboratore e stato con visualizzazione importo pagato.
  - Calendario con vista giornaliera o settimanale.
  - Creazione nuovo appuntamento con controlli automatici di disponibilità collaboratore (stato attivo, giorni lavorativi, fascia oraria) e conflitti di orario.
  - Modifica: aggiornare data, orario, note, stato (BOOKED/COMPLETED/CANCELLED/NO_SHOW).
  - Annullamento: solo se non completato.
  - Registrazione assenza (NO_SHOW): solo se non completato.
  - Completamento: conserva prezzo e durata originari del servizio.
  - Pagamento: registrazione (solo per COMPLETED), rimborso (solo per COMPLETED), importo effettivamente incassato, data/ora pagamento, metodo (contanti/carta/altro).
  - Completamento e pagamento: pulsante **Completa e conferma pagamento** che porta l'appuntamento a COMPLETED e registra il pagamento (importo + metodo).
- **Clienti (`pages/3_Clienti.py`)**: ricerca per nome/telefono/email, inserimento, modifica ed eliminazione (con validazione di unicità del nome).
- **Servizi (`pages/4_Servizi.py`)**: gestione listino servizi con durata in minuti e prezzo (con validazione di unicità del nome).
- **Collaboratori (`pages/5_Collaboratori.py`)**: gestione ruoli, disponibilità, orari di turno e giorni lavorativi (con validazione di unicità del nome).
- **Incassi (`pages/6_Incassi.py`)**: riepilogo e grafici degli incassi giornalieri (ultimi 7 giorni), mensili (ultimi 6 mesi) e per periodo (Settimana, Mese, Trimestre, Anno).
- **Impostazioni e Backup (`pages/7_Impostazioni.py`)**:
  - Stato e statistiche del database locale (`data/barber.db`).
  - Creazione di backup consistenti nella cartella `backups/`.
  - Download ed eliminazione dei backup salvati.
  - Ripristino sicuro da backup locale o da file `.db` caricato (con creazione automatica di un backup di sicurezza `barber_pre_restore_*.db` prima di sovrascrivere i dati).

---

## Requisiti

- Windows 10 / 11 (o Linux/macOS)
- **Python 3.12+**

---

## Installazione e Avvio (Windows)

1. Apri il terminale (PowerShell o Prompt dei comandi) nella cartella del progetto.
2. Crea e attiva l'ambiente virtuale (se non già presente):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Installa le dipendenze:
   ```powershell
   pip install -r requirements.txt
   ```
4. Avvia l'applicazione:
   ```powershell
   streamlit run app.py
   ```
   Si aprirà automaticamente il browser con l'interfaccia del gestionale.

---

## Struttura del progetto

```text
local-barber-app/
├── app.py                        # Entry point e navigazione Streamlit
├── database.py                   # Configurazione SQLite e sessioni SQLAlchemy 2
├── requirements.txt              # Dipendenze Python
├── data/
│   └── barber.db                 # Database SQLite locale (creato automaticamente all'avvio)
├── backups/                      # Cartella dei backup locali (.db)
├── models/                       # Modelli ORM SQLAlchemy
│   ├── __init__.py
│   ├── client.py
│   ├── service.py
│   ├── collaborator.py
│   └── appointment.py
├── services/                     # Logica applicativa e accesso dati
│   ├── client_service.py
│   ├── service.py
│   ├── collaborator_service.py
│   ├── appointment_service.py
│   ├── revenue_service.py
│   └── backup_service.py
├── pages/                        # Schermate Streamlit
│   ├── 1_Dashboard.py
│   ├── 2_Appuntamenti.py
│   ├── 3_Clienti.py
│   ├── 4_Servizi.py
│   ├── 5_Collaboratori.py
│   ├── 6_Incassi.py
│   └── 7_Impostazioni.py
└── tests/                        # Suite di test Pytest
    ├── conftest.py
    ├── test_demo.py
    ├── test_appointments.py
    └── test_backup.py
```

---

## Backup e Ripristino

1. Vai nella sezione **Impostazioni** dal menu laterale.
2. Clicca su **Crea backup ora** per salvare una copia completa del database nella cartella `backups/` con data e ora (`barber_backup_YYYYMMDD_HHMMSS.db`).
3. Puoi scaricare, eliminare o ripristinare i backup dalla stessa pagina.

---

## Migrazione database

Poiché sono state aggiunte nuove colonne al modello `Appointment` (status, price, duration_minutes), è necessaria una migrazione per gli utenti che hanno già un database esistente:

1. **Nuova installazione**: Eliminare `data/barber.db` e lasciare che l'applicazione crei un nuovo database con la struttura aggiornata.

2. **Migrazione manuale**: Aggiungere le seguenti colonne alla tabella `appointments` nel database esistente:

```sql
ALTER TABLE appointments ADD COLUMN status TEXT DEFAULT 'BOOKED';
ALTER TABLE appointments ADD COLUMN price REAL;
ALTER TABLE appointments ADD COLUMN duration_minutes INTEGER;
```

### Campo status (TASK 2)

Ogni appuntamento ha uno stato:
- `BOOKED`: appuntamento prenotato
- `COMPLETED`: appuntamento completato
- `CANCELLED`: annullato
- `NO_SHOW`: cliente assente

### Campi pagamenti (TASK 3)

Ogni appuntamento può avere informazioni di pagamento:
- `payment_status`: `UNPAID`, `PAID`, `REFUNDED` (default: `UNPAID`)
- `amount_paid`: importo effettivamente incassato
- `payment_datetime`: data e ora del pagamento
- `payment_method`: contanti, carta, altro

**Migrazione automatica**: All'avvio, se il database esistente non ha queste colonne, vengono aggiunte automaticamente e i dati vengono backfillati:
- Appuntamenti `COMPLETED` → `payment_status=PAID`, `amount_paid=price`, `payment_method=Contanti`
- Altri appuntamenti → `payment_status=UNPAID`, `amount_paid=0.0`

### Logica automatica pagamenti (TASK 3)

- **Completamento** (`complete_appointment`): quando l'appuntamento passa a `COMPLETED`, il pagamento viene impostato automaticamente come `PAID` (con `amount_paid`, `payment_datetime`, `payment_method`).
- **Cambio stato**: se dall'`update_appointment` si imposta uno stato diverso da `COMPLETED` (es. `BOOKED`, `CANCELLED`, `NO_SHOW`), il pagamento torna automaticamente a `UNPAID` e i campi pagamento vengono resettati.

### Incassi (TASK 3)

Le funzioni di revenue (`get_revenue_summary`, `get_daily_revenue`, `get_monthly_revenue`, `get_period_revenue_total`) considerano come incassi **solo gli appuntamenti COMPLETED con pagamento PAID**. I rimborsi (REFUNDED) annullano l'incasso. Gli appuntamenti BOOKED/CANCELLED/NO_SHOW o pagati con UNPAID non contribuiscono agli incassi.

### Incassi e metriche (TASK 4)

La dashboard economica (`pages/1_Dashboard.py`) e la pagina **Incassi** (`pages/6_Incassi.py`) espongono:

- **Incassi giornalieri** (ultimi 7 giorni) e **mensili** (ultimi 6 mesi) e per periodo (Settimana, Mese, Trimestre, Anno).
- **Numero di servizi completati** (pagati) per periodo.
- **Servizi più venduti** (per periodo): conteggio servizi COMPLETED+PAID e ricavo associato.
- **Pagamenti ancora da registrare**: somma degli importi degli appuntamenti COMPLETED con pagamento UNPAID (per periodo).
- **Rimborsi**: somma degli importi pagati (REFUNDED) per periodo.

3. Puoi scaricare il file `.db` su una chiavetta USB o altro disco usando **Scarica backup selezionato**.
4. Per ripristinare i dati:
   - scegli un backup dall'elenco locale nella sezione **Ripristina dal backup selezionato**, oppure
   - carica un file `.db` esterno nella sezione **Ripristina da file esterno (.db)**.
   Prima di applicare il ripristino, l'applicazione verifica l'integrità del file e salva automaticamente una copia di sicurezza dei dati correnti.

---

## Esecuzione dei Test

Per eseguire la suite di test automatici con Pytest:

```powershell
python -m pytest tests/ -v
```
