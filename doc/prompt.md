**Agisci come un Senior Python Developer esperto di Streamlit.**

Voglio realizzare un prototipo funzionante di un gestionale locale per un barbiere chiamato Barber Manager.

**Stack tecnologico obbligatorio**
- Python 3.12+
- Streamlit per tutta l'interfaccia grafica
- SQLite per il database
- SQLAlchemy 2 per l'accesso ai dati
- Pytest per i test

**Non utilizzare:**

- React
- Vue
- Angular
- HTML scritto manualmente
- CSS personalizzato, salvo necessità strettamente indispensabili
- JavaScript
- FastAPI
- Servizi cloud o API esterne 

**Obiettivo**
Realizzare un gestionale semplice, utilizzabile da un barbiere senza competenze informatiche.

L'applicazione deve funzionare completamente in locale sul PC Windows.

**Schermate**
- Dashboard con appuntamenti del giorno e riepilogo incassi.
- Appuntamenti con elenco e calendario semplice.
- Nuovo appuntamento con selezione cliente, servizio, data e orario.
- Clienti con ricerca, inserimento e modifica.
- Servizi con gestione prezzi e durata.
- Collaboratori con gestione orari e disponibilità.
- Incassi con riepilogo giornaliero e mensile.
- Impostazioni e backup.

**Architettura**
Organizza il progetto in moduli Python separati.

*Esempio:*

- barber_manager/ app.py database.py models/ services/ pages/ 
- 1_Dashboard.py 
- 2_Appuntamenti.py 
- 3_Clienti.py 
- 4_Servizi.py 
- 5_Collaboratori.py 
- 6_Incassi.py 
- 7_Impostazioni.py 
- tests/ 
- requirements.txt 
- README.md

**Requisiti di sviluppo**

- Usa esclusivamente componenti Streamlit per l'interfaccia.
- Mantieni la grafica semplice e professionale.
- Utilizza form per inserimento e modifica.
- Utilizza tabelle e filtri per visualizzare i dati.
- Utilizza SQLite per la persistenza.
- Evita di inserire tutta la logica dentro app.py.
- Separa interfaccia, logica applicativa e accesso ai dati.
- Gestisci correttamente gli errori.
- Non utilizzare dati fittizi nella versione collegata al database.

**Modalità di lavoro**

Procedi per fasi.

FASE 1: realizza la struttura del progetto e tutte le schermate con dati dimostrativi.

FASE 2: implementa il database e i modelli.

FASE 3: collega le schermate al database.

FASE 4: implementa la logica degli appuntamenti e i controlli di disponibilità.

FASE 5: implementa backup, test e documentazione.

*Non sviluppare tutte le fasi contemporaneamente.*

Inizia dalla FASE 1 e mostrami un prototipo navigabile completo.