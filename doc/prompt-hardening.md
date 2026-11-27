BARBER MANAGER – FASE 4.1: HARDENING E AFFIDABILITÀ

Agisci come Senior Python Developer e Software Architect.

Stiamo sviluppando Barber Manager, un gestionale locale per barbieri, utilizzando:

- Python 3.12+
- Streamlit
- SQLite
- SQLAlchemy 2
- Pytest

Il progetto esistente è già funzionante e comprende:

- Dashboard
- Calendario appuntamenti
- Gestione clienti
- Gestione servizi
- Gestione collaboratori
- Gestione appuntamenti
- Registrazione pagamenti
- Rimborsi
- Statistiche e incassi
- Backup e ripristino

OBIETTIVO

Eseguire una fase di consolidamento tecnico per correggere problemi individuati durante la code review.

IMPORTANTE:

- Non riscrivere il progetto.
- Non modificare inutilmente le schermate.
- Non introdurre nuove tecnologie.
- Non cambiare lo stack tecnologico.
- Non eliminare funzionalità esistenti.
- Preservare la compatibilità con il database già utilizzato.

Prima di intervenire, analizza il repository e verifica che i problemi descritti siano ancora presenti nel codice attuale.

TASK 1 – CORREZIONE MIGRAZIONE PAGAMENTI

Analizza il backfill dei vecchi appuntamenti in database.py.

È stato individuato un possibile errore:

appt.payment_status = Appointment.STATUS_COMPLETED

Il campo payment_status deve utilizzare le costanti relative agli stati di pagamento.

Verifica le costanti disponibili e correggi la migrazione utilizzando il valore corretto.

Requisiti:

- Gli appuntamenti completati e già considerati pagati devono essere migrati correttamente.
- Gli appuntamenti non completati non devono essere trasformati arbitrariamente in pagati.
- Le migrazioni devono essere idempotenti.
- Non devono essere sovrascritti dati validi già presenti.

Aggiungi test per:

- Migrazione di appuntamenti completati.
- Migrazione di appuntamenti non completati.
- Migrazione di appuntamenti già migrati.
- Verifica della validità degli stati risultanti.

TASK 2 – SEPARAZIONE COMPLETAMENTO E PAGAMENTO

Analizza appointment_service.py e payment_service.py.

Attualmente il completamento dell'appuntamento può comportare automaticamente la registrazione del pagamento in contanti.

Vogliamo separare le due responsabilità.

Implementa:

1. complete_appointment()
  
   - Cambia lo stato dell'appuntamento in COMPLETED.
   - Non registra automaticamente un pagamento.
   - Non modifica impropriamente i dati economici.

2. register_payment()
  
   - Registra il pagamento di un appuntamento completato.
   - Richiede importo e metodo di pagamento.
   - Verifica che l'appuntamento non sia già pagato o rimborsato.
   - Registra data e ora del pagamento.

3. Mantieni un'eventuale operazione rapida che permetta di completare l'appuntamento e registrare contestualmente il pagamento in contanti.

L'operazione rapida deve utilizzare le funzioni applicative esistenti, evitando duplicazioni di logica.

Aggiorna le schermate Streamlit solo dove necessario.

Aggiungi test per:

- Completamento senza pagamento.
- Pagamento successivo.
- Pagamento di un appuntamento non completato.
- Tentativo di doppio pagamento.
- Completamento con pagamento rapido.
- Correttezza degli stati dopo ogni operazione.

TASK 3 – SICUREZZA DEI RIMBORSI

Analizza register_refund() in payment_service.py.

Implementa controlli per garantire che:

- Si possa rimborsare soltanto un appuntamento effettivamente pagato.
- Non sia possibile rimborsare due volte lo stesso pagamento.
- Non sia possibile rimborsare un importo superiore a quello incassato.
- Un appuntamento non pagato non possa essere rimborsato.
- Lo stato del pagamento sia aggiornato correttamente.

Per questa fase puoi mantenere il rimborso totale, se il modello dati attuale non supporta ancora i rimborsi parziali.

Non introdurre una gestione complessa dei rimborsi se non è necessaria.

Aggiungi test per tutti i casi descritti.

TASK 4 – CONTROLLO COMPLETO DEGLI ORARI

Analizza is_collaborator_available() e tutte le funzioni che verificano la disponibilità.

Il controllo deve considerare l'intero intervallo dell'appuntamento.

Esempio:

Orario di lavoro: 09:00–19:00
Durata servizio: 45 minuti

Appuntamento alle 18:45 = NON DISPONIBILE.

Appuntamento alle 18:00 = DISPONIBILE, se non esistono sovrapposizioni.

Requisiti:

- Verificare l'orario di inizio.
- Calcolare l'orario di fine.
- Verificare che l'orario di fine rientri nel turno lavorativo.
- Verificare eventuali pause.
- Verificare le sovrapposizioni con altri appuntamenti.
- Escludere gli appuntamenti annullati dal controllo dei conflitti.
- Gestire correttamente appuntamenti consecutivi senza sovrapposizione.

Aggiungi test per:

- Appuntamento che termina esattamente alla chiusura.
- Appuntamento che supera l'orario di chiusura.
- Appuntamento durante una pausa.
- Appuntamenti consecutivi.
- Appuntamenti sovrapposti.
- Appuntamenti annullati.

TASK 5 – GESTIONE DELLE TRANSAZIONI

Analizza database.py, appointment_service.py e payment_service.py.

Verifica la presenza di commit multipli e responsabilità sovrapposte tra servizi e context manager.

Obiettivo:

- Rendere coerente la gestione delle transazioni.
- Garantire che operazioni correlate siano atomiche.
- Evitare che una registrazione di pagamento parzialmente fallita lasci dati incoerenti.
- Gestire correttamente rollback ed eccezioni.

Non effettuare un refactoring esteso.

Se la struttura attuale è già sufficientemente affidabile, documenta il motivo per cui non è necessario modificarla.

Aggiungi test per:

- Rollback in caso di errore.
- Registrazione pagamento fallita.
- Coerenza tra appuntamento e pagamento.
- Operazioni multiple eseguite nella stessa transazione.

TASK 6 – VERIFICA GENERALE

Esegui tutti i test esistenti e quelli nuovi.

Verifica:

- Importazione dei moduli.
- Creazione del database.
- Integrità referenziale.
- Gestione appuntamenti.
- Gestione pagamenti.
- Rimborsi.
- Calcolo incassi.
- Backup e ripristino.

Controlla che le modifiche non abbiano introdotto regressioni.

MODALITÀ DI LAVORO OBBLIGATORIA

Procedi un task alla volta.

Per ogni task:

1. Analizza il codice esistente.
2. Descrivi il problema.
3. Proponi la modifica.
4. Implementa la soluzione.
5. Scrivi o aggiorna i test.
6. Esegui i test.
7. Mostra i risultati.

Non passare al task successivo se il precedente presenta test falliti non risolti.

Alla fine produci un riepilogo contenente:

- File modificati.
- Problemi risolti.
- Test aggiunti.
- Test eseguiti.
- Eventuali problemi ancora aperti.

VINCOLI FINALI

Il prodotto deve continuare a funzionare:

- Localmente su Windows.
- Senza connessione Internet.
- Con SQLite.
- Con Streamlit.
- Senza inviare dati a servizi esterni.

Non implementare ancora nuove funzionalità commerciali.

La priorità è avere un software affidabile prima di installarlo sul PC del primo barbiere. 