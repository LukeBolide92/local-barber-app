# Fase 4 - Gestione sicura delle credenziali (Supabase)

- [x] Test: redaction/mascheramento segreti (utils.supabase.redact_secrets, mask_token)
- [x] Test: servizio credenziali (keyring) store/read/delete
- [x] Test: nessuna fallback in chiaro se keyring non disponibile
- [x] Implementa utils/supabase.py: helper di redaction
- [x] Implementa services/supabase_credential_service.py: vault keyring
- [x] Wire UI pages/7_Impostazioni.py: PAT transient in memoria, niente credenziali in log/errori, pulizia
- [x] Esegui test suite completa e verifica output (70 passed)
- [x] Report doc/fase-4-gestione-credenziali.md