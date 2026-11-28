# Fase 4 - Gestione sicura delle credenziali Supabase

## Obiettivo
Implementare la gestione sicura delle credenziali (Personal Access Token - PAT) per la configurazione del progetto Supabase, in modo che:

- Il PAT non venga mai salvato in chiaro su disco, nei log o nei messaggi di errore.
- Il PAT venga memorizzato temporaneamente nel Credential Manager di Windows (keyring).
- Il PAT venga eliminato dopo la configurazione.
- Il sistema si arrende (senza fallback) se il Credential Manager non è disponibile.

## Componenti Implementati

### 1. Utility di Redaction (utils/supabase.py)
- `redact_secrets(text, *secrets)`: Sostituisce le stringhe segrete con `***`.
- `mask_token(token)`: Mostra solo gli ultimi 4 caratteri di un token (es. `****7890`).

### 2. Service per Credenziali (services/supabase_credential_service.py)
- `CredentialStoreUnavailableError`: Eccezione per quando il vault non è disponibile.
- `credential_store_available()`: Verifica se il backend keyring è utilizzabile.
- `store_pat(project_ref, pat)`: Memorizza il PAT nel vault associato al progetto.
- `read_pat(project_ref)`: Legge il PAT dal vault.
- `has_pat(project_ref)`: Verifica se esiste un PAT per il progetto.
- `delete_pat(project_ref)`: Cancella il PAT dal vault (best-effort).
- `purge_all_pats()`: Cancella tutti i PAT (per future implementazioni).

### 3. Modifica della Pagina "Impostazioni" (pages/7_Impostazioni.py)
- Importa `store_pat`, `delete_pat`, `CredentialStoreUnavailableError`, `mask_token`.
- Gestione sicura del PAT:
  - Validazione del Project URL e del PAT.
  - Salvataggio temporaneo nel Credential Manager tramite `store_pat`.
  - Messaggi di errore generici (nessun token esposto).
  - Pulizia del PAT dopo la configurazione (se necessario).
- Uso di `mask_token` per eventuali messaggi di conferma (non mostrare token).

## Sicurezza delle Credenziali

### Principi di sicurezza applicati:
1. **Nessun salvataggio in chiaro**: Il PAT non viene scritto in file, `.env`, log o messaggi di errore.
2. **Vault sicuro**: Il PAT viene memorizzato nel Credential Manager di Windows (keyring).
3. **Fail-safe**: Se il vault non è disponibile, la procedura si arrende senza salvare il PAT in chiaro.
4. **Transient storage**: Il PAT è disponibile solo durante la sessione di configurazione.
5. **Pulizia**: Dopo la configurazione, il PAT viene eliminato dal vault.

### Flusso operativo:
1. L'utente inserisce Project URL e PAT.
2. Il sistema estrae il Project Reference ID dal URL.
3. Il PAT viene salvato nel Credential Manager tramite `store_pat`.
4. Il sistema avvia la procedura di verifica (chiamata a Supabase Management API).
5. Al termine della configurazione, il PAT viene eliminato tramite `delete_pat`.
6. Il sistema mostra solo messaggi generici (es. "PAT salvato in modo sicuro").

## Test Eseguiti

### Test di Redaction (tests/test_supabase.py)
- Verifica che `redact_secrets` rimuova le stringhe sensibili.
- Verifica che `mask_token` mascheri correttamente i token.

### Test di Credenziali (tests/test_supabase_credentials.py)
- Verifica che il vault sia disponibile quando il backend keyring è presente.
- Verifica che il vault sia non disponibile quando il backend è `None` o `fail.Keyring`.
- Verifica che `store_pat`, `read_pat`, `delete_pat` funzionino correttamente.
- Verifica che `CredentialStoreUnavailableError` venga sollevata quando il vault non è disponibile.
- Verifica che `has_pat` e `read_pat` gestiscano correttamente i casi di assenza del PAT.

## Invarianti di Sicurezza
- Il PAT non viene mai mostrato all'utente (tranne per gli ultimi 4 caratteri in caso di conferma).
- Il PAT non viene mai scritto in log o file di testo.
- Il PAT non viene mai esposto a componenti frontend o browser.
- Il PAT viene eliminato dal vault dopo la configurazione.
- Il sistema si arrende (exception) se il vault non è disponibile.

## Limiti e Rischi Residuali
1. **Dipendenza da keyring**: Se il Credential Manager di Windows non è disponibile (es. su macOS/Linux o senza permessi), la procedura si arrende.
2. **Nessun fallback**: Non c'è un meccanismo di backup che salvi il PAT in un altro modo sicuro.
3. **Session persistence**: Il PAT rimane in memoria durante la sessione dell'utente - se l'app si chiude inaspettatamente, potrebbe rimanere residuo (ma non viene salvato su disco).

## Prossimi Passi
- Integrare il servizio di bootstrap Supabase (SupabaseBootstrapService) che utilizza `store_pat` e `delete_pat`.
- Implementare la verifica reale della Management API (richiede connettività a Supabase).
- Aggiungere test di integrazione per verificare la pulizia del PAT dopo la configurazione.
- Documentare ulteriormente il flusso di sicurezza per gli utenti finali.