BARBER MANAGER – FASE 2: CONSOLIDAMENTO E MVP

Agisci come Senior Python Developer e Software Architect.

Stiamo sviluppando Barber Manager, un gestionale locale per barbieri.

Il progetto esistente è già sviluppato con:

- Python
- Streamlit
- SQLite
- SQLAlchemy
- Pytest

Il repository contiene già dashboard, appuntamenti, clienti, servizi, collaboratori, incassi e backup.

OBIETTIVO

Vogliamo trasformare la PoC esistente in un MVP realmente utilizzabile da un primo barbiere.

Il software deve essere utilizzabile esclusivamente dal PC del negozio, senza servizi cloud e senza trasmissione di dati esterni.

Attenzione: il prodotto dovrà poter essere venduto in futuro ad altri barbieri.

Per questo motivo deve essere configurabile e installabile su computer diversi, senza modifiche al codice sorgente.

Non implementare ancora multi-tenancy, cloud, abbonamenti o integrazioni esterne.

PRINCIPIO FONDAMENTALE

NON riscrivere il progetto da zero.

Analizza prima il codice esistente e mantieni tutte le funzionalità già funzionanti.

Prima di modificare il codice:

1. Analizza la struttura del repository.
2. Individua problemi e debito tecnico.
3. Verifica i test esistenti.
4. Prepara un piano di intervento.
5. Evidenzia eventuali modifiche incompatibili al database.

TASK 1 – STABILIZZAZIONE

- Verifica gli import dei modelli SQLAlchemy.
- Verifica le relazioni tra entità.
- Uniforma la gestione delle sessioni e delle transazioni.
- Abilita i vincoli di integrità referenziale SQLite.
- Sposta il database in una directory dati stabile.
- Evita dipendenze dalla directory di esecuzione.
- Introduci logging degli errori.
- Verifica la gestione delle eccezioni.

TASK 2 – APPUNTAMENTI

Ogni appuntamento deve avere uno stato:

- BOOKED
- COMPLETED
- CANCELLED
- NO_SHOW

Implementa:

- Modifica appuntamento.
- Annullamento appuntamento.
- Completamento appuntamento.
- Registrazione cliente assente.
- Verifica disponibilità del collaboratore.
- Controllo che l'intero intervallo dell'appuntamento rientri nell'orario lavorativo.
- Controllo delle sovrapposizioni.

Gli appuntamenti completati devono conservare il prezzo e la durata originari del servizio, anche quando il servizio viene successivamente modificato.

TASK 3 – PAGAMENTI

Separare lo stato dell'appuntamento dallo stato del pagamento.

Implementare:

- Stato UNPAID.
- Stato PAID.
- Stato REFUNDED.
- Importo effettivamente incassato.
- Data e ora del pagamento.
- Metodo di pagamento: contanti, carta, altro.

Consentire la registrazione di un pagamento soltanto quando il servizio è stato completato.

Gestire correttamente eventuali rimborsi.

TASK 4 – INCASSI

Modificare la dashboard economica affinché consideri esclusivamente gli incassi effettivamente registrati.

Prevedere:

- Incassi giornalieri.
- Incassi mensili.
- Numero di servizi completati.
- Servizi più venduti.
- Pagamenti ancora da registrare.
- Rimborsi.

Non conteggiare appuntamenti prenotati, annullati o assenze come incassi.

TASK 5 – PREPARAZIONE COMMERCIALE

Preparare l'applicazione per essere installata su computer diversi.

Prevedere:

- Configurazione del nome del negozio.
- Configurazione di orari e giorni di apertura.
- Database separato per ogni installazione.
- Backup e ripristino.
- Esportazione CSV.
- Configurazione indipendente dai percorsi locali dello sviluppatore.

Il server deve ascoltare esclusivamente su 127.0.0.1.

Non introdurre servizi cloud o chiamate HTTP esterne.

TASK 6 – TEST

Aggiungere test per:

- Creazione appuntamento.
- Modifica appuntamento.
- Conflitti di orario.
- Orari lavorativi.
- Completamento appuntamento.
- Registrazione pagamento.
- Rimborsi.
- Calcolo incassi.
- Backup e ripristino.
- Integrità referenziale.

MODALITÀ DI LAVORO

Procedi in piccoli incrementi.

Non implementare tutti i task contemporaneamente.

Per ogni task:

1. Spiega le modifiche previste.
2. Implementa.
3. Esegui i test.
4. Mostra i risultati.
5. Aggiorna il README.

Non eliminare funzionalità esistenti senza una motivazione.

Inizia esclusivamente dal TASK 1 e attendi una mia verifica prima di proseguire. 