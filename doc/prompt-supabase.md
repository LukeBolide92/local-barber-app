BARBER – COLLEGAMENTO SUPABASE E CONFIGURAZIONE AUTOMATICA

1. Obiettivo

Implementare nel gestionale Barber la possibilità di collegare il progetto Supabase personale del barbiere e configurare automaticamente il database.

L'esperienza deve essere estremamente semplice.

Il barbiere non è un informatico e non deve conoscere:

- PostgreSQL.
- SQL.
- URI di connessione.
- Migrazioni.
- Struttura delle tabelle.
- Relazioni tra database.

Deve semplicemente seguire una guida, inserire le informazioni richieste e premere un pulsante.

Il gestionale deve occuparsi autonomamente di:

- Collegarsi al progetto Supabase.
- Verificare le autorizzazioni.
- Analizzare il database.
- Riconoscere le tabelle già presenti.
- Creare automaticamente lo schema se necessario.
- Verificare che tutto sia pronto.

2. Analisi preliminare del progetto

Prima di modificare il codice, analizza il repository.

Individua:

- Tutti i modelli SQLAlchemy.
- Tutte le tabelle attualmente utilizzate.
- Clienti.
- Appuntamenti.
- Servizi.
- Pagamenti.
- Rimborsi.
- Eventuali altre entità.
- Relazioni, chiavi primarie e chiavi esterne.
- Indici e vincoli.
- Eventuali tabelle ausiliarie.
- Inizializzazione attuale di SQLite.
- Gestione delle transazioni.
- Eventuali migrazioni già presenti.
- Tutti i servizi e repository che accedono al database.

Non inventare modelli o strutture dati.

La struttura PostgreSQL deve essere coerente con quella effettivamente utilizzata dal gestionale.

Prima di procedere, restituisci un report dell'architettura attuale.

3. Interfaccia delle impostazioni

Mantieni le due schede:

Database locale

- SQLite.
- Funzionamento attuale completamente invariato.

Database remoto

Sezione dedicata a Supabase.

La schermata deve presentare due possibilità:

A. Configura Supabase

Una guida passo passo che accompagni il barbiere nella creazione del proprio progetto.

B. Ho già un progetto Supabase

Permette di inserire direttamente i parametri richiesti.

Campi:

- Project URL.
- Personal Access Token (PAT).

Il Project Reference ID deve essere ricavato automaticamente dal Project URL, quando possibile.

Non chiedere:

- URI PostgreSQL.
- Password PostgreSQL.
- Porta.
- Username del database.
- Publishable Key, salvo che sia necessaria per una successiva funzionalità API.

4. Guida integrata per l'utente

Implementa una procedura guidata direttamente nella schermata.

La guida deve accompagnare il barbiere attraverso questi passaggi:

Passaggio 1 – Creazione account

Spiegare come creare un account Supabase.

Link:
https://supabase.com

Utilizzare istruzioni semplici, evitando terminologia tecnica non necessaria.

Passaggio 2 – Creazione progetto

Spiegare come creare un nuovo progetto Supabase.

Indicare:

- Scelta del nome del progetto.
- Scelta della regione.
- Creazione della password del database.
- Conservazione della password in un posto sicuro.

La password PostgreSQL non deve essere richiesta dal gestionale in questa fase, se non serve alla soluzione tecnica scelta.

Passaggio 3 – Recupero Project URL

Spiegare dove trovare il Project URL nel pannello Supabase.

Consentire di copiarlo e inserirlo nel gestionale.

Dettaglio operativo della guida (come verificato nella pratica):

1. Accedere al dashboard di Supabase (https://supabase.com) e selezionare il progetto creato.
2. Cliccare sul pulsante **"Connect"** (visibile nella pagina del progetto).
3. Selezionare la voce **"Connect via API"**.
4. Nella schermata risultante, copiare il valore del campo **"SUPABASE_URL"** (formato `https://<project-ref>.supabase.co`).
5. Incollare il valore nel campo "Project URL" del gestionale.

Il Project Reference ID viene estratto automaticamente dall'URL inserito.

Passaggio 4 – Creazione Personal Access Token

Spiegare come generare un PAT.

Link alla documentazione ufficiale:
https://supabase.com/docs/guides/platform/access-control

Link alla documentazione Management API:
https://supabase.com/docs/reference/api/introduction

Prima di definire la procedura:

- Verificare i permessi effettivamente richiesti dagli endpoint utilizzati.
- Verificare se il PAT può essere limitato a uno specifico progetto.
- Verificare se esistono scope o autorizzazioni più restrittive.
- Non dichiarare che il token è limitato al progetto se tecnicamente non lo è.
- Non richiedere permessi non necessari.

Spiegare all'utente che il token è una credenziale potente e deve essere trattato come una password.

Passaggio 5 – Collegamento

L'utente inserisce:

- Project URL.
- PAT.

Premendo il pulsante "Verifica e configura", il gestionale avvia automaticamente la procedura.

5. Collegamento tramite Supabase Management API

Utilizzare la Management API ufficiale di Supabase per le operazioni amministrative necessarie.

Studiare la documentazione aggiornata prima di implementare.

Verificare gli endpoint effettivamente disponibili per:

- Verifica del token.
- Identificazione del progetto.
- Verifica dell'accessibilità del progetto.
- Esecuzione di migrazioni SQL.
- Verifica dello stato del database.

Non inventare endpoint o parametri.

Non utilizzare la service_role key come sostituto del PAT.

Non confondere:

- PAT.
- Publishable Key.
- Secret Key.
- Password PostgreSQL.

Se la Management API non permette di effettuare un'operazione con il PAT disponibile, fermarsi e descrivere la limitazione prima di introdurre workaround.

Utilizzare HTTPS.

Non trasmettere il PAT a servizi diversi da Supabase.

Non inserirlo in URL, query string o log.

6. Gestione sicura del PAT

Il PAT deve essere utilizzato esclusivamente per la configurazione amministrativa.

Requisiti:

- Non salvare il PAT nel repository.
- Non salvarlo in chiaro in file JSON, YAML, TOML o ".env".
- Non scriverlo nei log.
- Non mostrarlo nuovamente dopo l'inserimento.
- Non inserirlo in messaggi di errore.
- Non esporlo a componenti frontend non necessari.
- Utilizzare HTTPS.

Durante la procedura può essere conservato temporaneamente in memoria.

Se serve conservarlo durante l'esecuzione, utilizzare Windows Credential Manager tramite "keyring".

Al termine della configurazione:

- Eliminare il PAT dal Credential Manager.
- Eliminare i riferimenti in memoria non più necessari.
- Conservare soltanto le informazioni necessarie per identificare il progetto e utilizzare successivamente le API ordinarie.

Se in futuro servirà applicare una nuova migrazione amministrativa e non sarà più disponibile un'autorizzazione valida, chiedere nuovamente all'utente di autorizzare l'operazione.

Non conservare permanentemente il PAT soltanto per evitare di richiederlo in futuro.

Se il sistema di protezione delle credenziali non è disponibile, interrompere la procedura senza fallback in chiaro.

7. Riconoscimento automatico dello schema

Dopo aver verificato la connessione, il gestionale deve analizzare il database.

Prevedere quattro situazioni.

A – Database vuoto

Se non esistono tabelle applicative:

- Creare automaticamente tutte le tabelle previste.
- Creare relazioni.
- Creare chiavi primarie e chiavi esterne.
- Creare indici e vincoli.
- Inizializzare il sistema di versionamento.
- Verificare la struttura creata.

Il barbiere non deve fare nulla.

B – Database già configurato

Se tutte le tabelle esistono e corrispondono alla struttura attesa:

- Non ricreare nulla.
- Non modificare dati.
- Riconoscere il database come pronto.
- Mostrare la versione dello schema.

C – Database incompleto

Se mancano alcune tabelle o colonne:

- Analizzare le differenze.
- Verificare la disponibilità di migrazioni sicure.
- Applicare soltanto le modifiche necessarie.
- Non eliminare dati.
- Non sovrascrivere strutture incompatibili.

D – Database incompatibile

Se esistono strutture non riconosciute o conflitti:

- Interrompere l'inizializzazione.
- Non effettuare modifiche distruttive.
- Mostrare un messaggio comprensibile.
- Produrre dettagli tecnici nei log senza credenziali.

Non considerare automaticamente vuoto un database solo perché manca una tabella specifica.

Non interferire con le tabelle interne di Supabase.

8. Creazione automatica e migrazioni

Introdurre Alembic o un sistema equivalente di migrazioni versionate.

Prevedere:

- Versione iniziale dello schema.
- Migrazioni successive.
- Riconoscimento della versione installata.
- Aggiornamento automatico quando esiste una migrazione sicura.
- Verifica finale della struttura.

Esempio:

- Versione 1: schema iniziale.
- Versione 2: nuove colonne.
- Versione 3: nuove tabelle.

Non utilizzare "Base.metadata.create_all()" come unico meccanismo di gestione dello schema.

La creazione iniziale deve essere eseguita soltanto quando il programma ha verificato che il database sia effettivamente vuoto e utilizzabile.

Le migrazioni devono:

- Essere versionate.
- Essere ripetibili in sicurezza.
- Non eliminare dati automaticamente.
- Gestire correttamente gli errori.
- Prevenire inizializzazioni concorrenti.

Se una migrazione non è sicura, non applicarla automaticamente.

9. Servizio dedicato

Implementare un servizio indipendente dalla UI, ad esempio:

"SupabaseBootstrapService"

Responsabilità:

1. Ricevere Project URL e PAT.
2. Validare il Project URL.
3. Ricavare il Project Reference ID.
4. Verificare il PAT.
5. Verificare l'accessibilità del progetto.
6. Verificare il database.
7. Analizzare lo schema.
8. Creare le tabelle se necessario.
9. Applicare migrazioni sicure.
10. Verificare nuovamente lo schema.
11. Restituire il risultato.

Separare completamente questa logica dalla UI Streamlit.

10. Utilizzo futuro delle API

In questa fase vogliamo configurare Supabase e preparare il database.

Non vogliamo ancora riscrivere il gestionale.

Progettare però l'architettura in modo che in futuro si possa utilizzare Supabase REST API per le operazioni ordinarie.

Considerare:

- Publishable Key.
- Supabase REST API.
- Row Level Security.
- Autenticazione.
- Separazione tra autorizzazioni amministrative e operative.

Il PAT non deve essere utilizzato per le normali operazioni sui clienti e sugli appuntamenti.

Non esporre credenziali amministrative al browser o a componenti frontend.

11. Separazione dal database locale

SQLite deve continuare a essere il database operativo attuale.

Non modificare:

- Clienti.
- Appuntamenti.
- Servizi.
- Pagamenti.
- Rimborsi.
- Statistiche.

Non introdurre:

- Sincronizzazione.
- Migrazione dei dati locali.
- Switch automatico del database operativo.

La funzionalità di bootstrap deve essere completamente indipendente.

12. Stati e feedback

Durante la procedura mostrare chiaramente:

- Configurazione non presente.
- Verifica credenziali.
- Connessione al progetto.
- Analisi database.
- Database vuoto.
- Creazione tabelle.
- Applicazione aggiornamenti.
- Verifica finale.
- Database pronto.
- Errore di autorizzazione.
- Errore di connessione.
- Schema incompatibile.

Al termine mostrare:

- Nome progetto.
- Project Reference ID.
- Numero di tabelle applicative.
- Versione dello schema.
- Esito della configurazione.

Non mostrare credenziali.

13. Test

Prevedere test per:

- Validazione Project URL.
- Estrazione Project Reference ID.
- PAT valido e non valido.
- Errori Management API.
- Database vuoto.
- Database già configurato.
- Database incompleto.
- Database incompatibile.
- Creazione automatica.
- Migrazioni.
- Ripetizione della configurazione.
- Interruzioni durante il bootstrap.
- Inizializzazioni concorrenti.
- Protezione dei dati preesistenti.
- Assenza di credenziali nei log.
- Invariabilità di SQLite.

Utilizzare un ambiente PostgreSQL/Supabase di test separato da quello reale.

Non effettuare test distruttivi sul progetto Supabase personale.

Non dichiarare test superati se non sono stati realmente eseguiti.

14. Documentazione

Aggiornare la documentazione del progetto.

Includere:

- Procedura guidata per creare l'account.
- Creazione del progetto.
- Recupero Project URL.
- Creazione PAT.
- Permessi richiesti.
- Collegamento al gestionale.
- Configurazione automatica.
- Gestione delle migrazioni.
- Gestione delle credenziali.

La guida deve essere scritta pensando a un barbiere senza conoscenze informatiche.

15. Modalità di sviluppo

Creare un nuovo branch:

"feature/supabase-auto-bootstrap"

Non modificare direttamente master.

Procedere per fasi:

1. Analisi architetturale.
2. Verifica Management API.
3. Progettazione della guida.
4. Gestione sicura delle credenziali.
5. Collegamento al progetto.
6. Riconoscimento dello schema.
7. Creazione automatica.
8. Migrazioni.
9. Interfaccia.
10. Test e documentazione.

Non riscrivere il gestionale.

Se emergono limitazioni tecniche o di sicurezza, descriverle prima di implementare workaround.

16. Criteri di accettazione

La funzionalità è completata quando:

- Il barbiere dispone di una guida integrata.
- Deve inserire soltanto Project URL e PAT.
- Il progetto viene riconosciuto automaticamente.
- Le autorizzazioni vengono verificate.
- Il database viene analizzato.
- Se vuoto, viene inizializzato automaticamente.
- Se già configurato, viene riconosciuto.
- Se incompatibile, non viene modificato.
- Le migrazioni sono versionate.
- Il PAT viene eliminato al termine della configurazione.
- SQLite continua a funzionare esattamente come prima.
- I test previsti sono effettivamente eseguiti.

17. Report finale

Al termine fornire un report con:

- Architettura implementata.
- File creati e modificati.
- Endpoint Management API utilizzati.
- Permessi effettivamente richiesti.
- Procedura di collegamento.
- Procedura di bootstrap.
- Tabelle create e riconosciute.
- Sistema di migrazioni.
- Gestione delle credenziali.
- Test eseguiti e risultati.
- Eventuali limitazioni e rischi residui.

Non iniziare funzionalità di sincronizzazione, prenotazione online o migrazione dei dati locali.

L'obiettivo di questa fase è esclusivamente rendere possibile il collegamento e l'autoconfigurazione del database Supabase.
