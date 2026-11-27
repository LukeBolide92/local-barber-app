ULTIMO HARDENING – FASE 4.2

Obiettivo: chiusura definitiva dell'hardening prima del pilot

Il progetto è un gestionale per barbieri sviluppato in Python, Streamlit, SQLite e SQLAlchemy.

L'applicazione deve funzionare interamente in locale, senza servizi cloud e senza inviare dati dei clienti all'esterno.

Questa è l'ultima fase di hardening prima di consegnare il software al primo barbiere per un test reale.

IMPORTANTE:

- Non introdurre nuove funzionalità.
- Non cambiare stack tecnologico.
- Non fare refactoring estesi.
- Non modificare il comportamento esistente se non necessario per correggere i problemi indicati.
- Mantenere la compatibilità con i database già esistenti.
- Procedere un task alla volta, eseguendo i test dopo ogni modifica.
- Non considerare concluso un task finché non sono presenti test che ne verificano il comportamento.

---

TASK 1 – Migrazioni database robuste

Verifica e correggi la gestione delle migrazioni SQLite.

Requisiti:

- Ogni colonna mancante deve essere verificata e aggiunta singolarmente.
- Le migrazioni devono essere idempotenti: eseguirle più volte non deve causare errori né alterare dati esistenti.
- Non utilizzare "except Exception: pass" per nascondere errori durante le migrazioni.
- Gestire correttamente database aggiornati, database precedenti e database con migrazioni parzialmente applicate.
- Non perdere appuntamenti, clienti, pagamenti o altri dati già presenti.

Test richiesti:

- Database aggiornato.
- Database precedente alla migrazione.
- Database con una sola delle nuove colonne già presente.
- Esecuzione ripetuta delle migrazioni.
- Verifica che i dati preesistenti siano preservati.

TASK 2 – Rimborsi coerenti

Verifica la logica di rimborso in "payment_service.py".

Per questa versione del prodotto supportiamo esclusivamente rimborsi totali.

Requisiti:

- Non consentire rimborsi su pagamenti non effettuati.
- Non consentire doppi rimborsi.
- Non consentire rimborsi superiori all'importo pagato.
- Non consentire rimborsi parziali: se l'importo richiesto è diverso dall'importo effettivamente pagato, l'operazione deve essere rifiutata.
- Dopo un rimborso valido, lo stato del pagamento deve risultare coerente.
- Le statistiche degli incassi non devono conteggiare come incassati importi rimborsati.

Test richiesti:

- Rimborso totale valido.
- Rimborso su pagamento non effettuato.
- Doppio rimborso.
- Rimborso superiore all'importo pagato.
- Rimborso parziale rifiutato.
- Verifica degli importi nelle statistiche.

TASK 3 – Protezione dei pagamenti durante la modifica degli appuntamenti

Verifica "update_appointment()" e tutte le operazioni che modificano lo stato di un appuntamento.

Requisiti:

- Un appuntamento già pagato non deve poter perdere o azzerare il proprio stato di pagamento a seguito di una modifica.
- Non deve essere possibile riportare un appuntamento pagato a uno stato precedente cancellando implicitamente le informazioni sul pagamento.
- Una modifica incompatibile con un pagamento già registrato deve essere rifiutata con un errore chiaro.
- Per modificare una situazione che richiede un rimborso, il rimborso deve essere gestito esplicitamente tramite il servizio pagamenti.
- Mantenere separati lo stato dell'appuntamento e quello del pagamento.

Test richiesti:

- Modifica ordinaria di un appuntamento pagato.
- Tentativo di cambiare lo stato di un appuntamento pagato in uno stato incompatibile.
- Verifica che lo stato del pagamento non venga azzerato.
- Verifica che un rimborso esplicito mantenga la coerenza dei dati.

TASK 4 – Atomicità del completamento e pagamento rapido

Verifica "complete_appointment_and_register_quick_payment()".

L'operazione deve essere atomica.

Requisiti:

- Il completamento dell'appuntamento e la registrazione del pagamento devono avvenire nella stessa transazione.
- Se il pagamento fallisce, anche il completamento dell'appuntamento deve essere annullato.
- Se il completamento fallisce, non deve essere registrato alcun pagamento.
- Evitare commit intermedi nelle funzioni coinvolte.
- Gestire correttamente rollback ed eccezioni.
- Evitare duplicazioni di pagamenti in caso di ripetizione dell'operazione.

Test richiesti:

- Completamento e pagamento entrambi riusciti.
- Errore durante la registrazione del pagamento.
- Errore durante il completamento.
- Verifica del rollback completo.
- Tentativo di ripetere l'operazione.

---

TASK 5 – Verifica finale di regressione

Al termine dei task precedenti:

1. Eseguire l'intera suite di test.
2. Verificare che tutti i test precedenti continuino a passare.
3. Aggiungere eventuali test mancanti per i casi descritti.
4. Verificare che non siano stati introdotti errori nelle funzionalità esistenti.
5. Controllare che il database SQLite venga gestito correttamente anche dopo un riavvio dell'applicazione.

Non limitarsi a modificare il codice: eseguire realmente i test e riportarne i risultati.

REGOLE DI LAVORO

Procedi un task alla volta.

Prima di ogni modifica:

- Individua i file coinvolti.
- Spiega brevemente il problema.
- Descrivi la modifica minima necessaria.

Dopo ogni modifica:

- Esegui i test pertinenti.
- Riporta i risultati.
- Segnala eventuali problemi residui.

Non passare al task successivo se quello corrente presenta test falliti.

CRITERIO DI CHIUSURA

L'Ultimo hardening è concluso quando:

- Tutti e cinque i task sono completati.
- Tutti i test automatici passano.
- Non rimangono problemi noti relativi a migrazioni, pagamenti, rimborsi e transazioni.
- Non sono state introdotte funzionalità non richieste.

Al termine, produci un breve report con:

- File modificati.
- Problemi corretti.
- Test eseguiti e relativo esito.
- Eventuali limitazioni residue.
- Conferma che il progetto è pronto per iniziare il pilot, oppure elenco preciso dei blocchi ancora presenti.

Non iniziare ulteriori miglioramenti dopo aver soddisfatto questi criteri. L'obiettivo è chiudere l'hardening e passare al test reale con il barbiere. 