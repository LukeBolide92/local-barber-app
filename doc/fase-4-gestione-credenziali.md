# Fase 4 - Gestione sicura delle credenziali Supabase

## Obiettivo
Implementare la gestione sicura delle credenziali (Personal Access Token - PAT) per la configurazione del progetto Supabase, in modo che:

- Il PAT non venga mai salvato in chiaro su disco, nei log o nei messaggi di errore.
- Il PAT venga memorizzato temporaneamente nel Credential Manager di Windows (keyring).
- Il sistema offra all'utente un controllo esplicito per rimuovere le credenziali salvate.
- Il sistema si arrende (senza fallback) se il Credential Manager non è disponibile.

## Componenti Implementati

### 1. Utility di Redaction (utils/supabase.py)
- `redact_secrets(text, *secrets)`: Sostituisce le stringhe segrete con `***` in testi che dovrebbero rimanere privati.
- `mask_token(token)`: Mostra solo gli ultimi 4 caratteri di un token (es. `****7890`). **Nota**: Non utilizzato nella UI attuale; incluso per futura estensione o debug.

### 2. Service per Credenziali (services/supabase_credential_service.py)
- `CredentialStoreUnavailableError`: Eccezione per quando il vault non è disponibile.
- `credential_store_available()`: Verifica se il backend keyring è utilizzabile.
- `store_pat(project_ref, pat)`: Memorizza il PAT nel vault associato al progetto.
- `read_pat(project_ref)`: Legge il PAT dal vault.
- `delete_pat(project_ref)`: Cancella il PAT dal vault, se presente.
- `has_pat(project_ref)`: Verifica se esiste un PAT per il progetto.

### 3. Modifica della Pagina "Impostazioni" (pages/7_Impostazioni.py)
- Importa `store_pat`, `delete_pat`, `CredentialStoreUnavailableError`.
- Flusso utente:
  1. L'utente inserisce Project URL e PAT.
  2. Il sistema estrae il Project Reference ID dal URL.
  3. Il PAT viene salvato nel Credential Manager tramite `store_pat`.
  4. Viene mostrato un avviso con un'opzione di rimozione volontaria.
  5. L'utente può cliccare "Rimuovi credenziali salvate" per chiamare `delete_pat(project_ref)`.
  6. Messaggi di errore generici (il token non viene mai esposto).
- Se il vault non è disponibile, la procedura si arresta mostrando un errore immediato senza salvare in chiaro.

## Sicurezza delle Credenziali

### Principi di sicurezza applicati:
1. **Nessun salvataggio in chiaro**: Il PAT non viene scritto in file, `.env`, log o messaggi di errore.
2. **Vault sicuro**: Il PAT viene memorizzato nel Credential Manager di Windows (keyring).
3. **Fail-safe**: Se il vault non è disponibile, la procedura si arresta senza salvare il PAT in chiaro.
4. **Controllo utente**: L'utente può rimuovere le credenziali in qualsiasi momento tramite "Rimuovi credenziali salvate".
5. **Transient storage**: Il PAT non è inteso per la persistenza a lungo termine; la gestione della sua rimozione compete al flusso di configurazione successivo (bootstrap).

### Flusso operativo:
1. L'utente inserisce Project URL e PAT.
2. Il sistema estrae il Project Reference ID dal URL.
3. Il PAT viene salvato nel Credential Manager tramite `store_pat(project_ref, pat)`.
4. La UI mostra un messaggio di conferma e un'opzione di rimozione volontaria.
5. L'utente può scegliere di rimuovere le credenziali chiamando `delete_pat(project_ref)`.
6. Al completamento della configurazione/bootstrap (fasi successive), il PAT verrà rimosso dal vault.

## Test Eseguiti

### Test di Redaction (tests/test_supabase.py)
- Verifica che `redact_secrets` rimuova le stringhe sensibili.
- Verifica che `mask_token` mascheri correttamente i token (funzione inclusa ma non usata in UI).

### Test di Credenziali (tests/test_supabase_credentials.py)
- Verifica che il vault sia disponibile quando il backend keyring è presente.
- Verifica che il vault sia non disponibile quando il backend è `None` o `fail.Keyring`.
- Verifica che `store_pat`, `read_pat`, `delete_pat`, `has_pat` funzionino correttamente.
- Verifica che `CredentialStoreUnavailableError` venga sollevata quando il vault non è disponibile.
- Verifica che `has_pat` e `read_pat` gestiscano correttamente i casi di assenza del PAT.

## Invarianti di Sicurezza
- Il PAT non viene mai mostrato all'utente (tranne per gli ultimi 4 caratteri tramite `mask_token`, funzione di utilità non esposta in UI).
- Il PAT non viene mai scritto in log o file di testo.
- Il PAT non viene mai esposto a componenti frontend o browser.
- Le credenziali possono essere rimosse in qualsiasi momento dall'utente via "Rimuovi credenziali salvate".
- Il sistema si arrende (exception) se il vault non è disponibile.

## Limiti e Rischi Residuali
1. **Dipendenza da keyring**: Se il Credential Manager di Windows non è disponibile (es. su macOS/Linux o senza permessi), la procedura si arresta mostrando un messaggio di errore. Non è previsto alcun fallback in chiaro.
2. **PAT persistito fino alla rimozione**: Il PAT rimane nel vault finché l'utente non lo rimuove esplicitamente o non viene completato il bootstrap successivo. Questo è un compromesso deliberato: la fase 4 fornisce il meccanismo sicuro, ma la rimozione compete all'utente o al flusso di bootstrap successivo.
3. **Nessun timeout automatico**: Non esiste un meccanismo per rimuovere automaticamente il PAT dopo un certo periodo. L'amministratore deve gestire la rotazione delle credenziali.

## Prossimi Passi
- Integrare il servizio di bootstrap Supabase (SupabaseBootstrapService) che utilizzerà `store_pat`, `read_pat`, `delete_pat` per la configurazione amministrativa.
- Implementare la verifica reale della Management API (richiede connettività a Supabase).
- Aggiungere test di integrazione per verificare il flusso di rimozione delle credenziali.
- Documentare per gli utenti finali come rimuovere le credenziali salvate.