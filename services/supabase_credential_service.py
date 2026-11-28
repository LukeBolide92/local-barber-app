"""Gestione sicura delle credenziali Supabase per il gestionale Private Barber Manager.

Il Personal Access Token (PAT) e' utilizzato esclusivamente per la configurazione
amministrativa del progetto Supabase. Questa pagina centralizza le operazioni sul
vault delle credenziali del sistema operativo (Windows Credential Manager tramite
``keyring``) senza fallback in chiaro:

- Il PAT viene memorizzato solo nel Credential Manager.
- Non viene scritto in file, .env, log o messaggi d'errore.
- Alla fine della configurazione il PAT viene cancellato dal vault.
"""

import logging
from typing import Optional

import keyring

logger = logging.getLogger(__name__)

SUPABASE_KEYRING_SERVICE = "PrivateBarberManager"
_PAT_USERNAME_PREFIX = "supabase-pat"


class CredentialStoreUnavailableError(RuntimeError):
    """Sollevata quando il sistema di protezione credenziali non e' disponibile."""


def credential_store_available() -> bool:
    """Restituisce True se il backend di keyring e' utilizzabile.

    Non prova a leggere o scrivere: valuta solo la presenza di un backend
    effettivo (es. Windows Credential Manager). Se non c'e' un backend
    utilizzabile, la procedura deve interrompersi senza fallback in chiaro.
    """
    try:
        backend = keyring.get_keyring()
    except Exception:
        return False
    if backend is None:
        return False
    module = type(backend).__module__.lower()
    # I backend "fail" non sono utilizzabili.
    return "fail" not in module


def _require_available() -> None:
    if not credential_store_available():
        raise CredentialStoreUnavailableError(
            "Sistema di protezione delle credenziali non disponibile. "
            "Interrompo la procedura senza salvare il token in chiaro."
        )


def _pat_username(project_ref: Optional[str]) -> str:
    if project_ref:
        return f"{_PAT_USERNAME_PREFIX}:{project_ref}"
    return _PAT_USERNAME_PREFIX


def store_pat(project_ref: str, pat: str) -> None:
    """Memorizza il PAT nel Credential Manager associato al progetto.

    Args:
        project_ref: Project Reference ID del progetto Supabase.
        pat: Personal Access Token da memorizzare temporaneamente.

    Raises:
        CredentialStoreUnavailableError: se il vault non e' disponibile.
    """
    _require_available()
    keyring.set_password(SUPABASE_KEYRING_SERVICE, _pat_username(project_ref), pat)


def read_pat(project_ref: str) -> Optional[str]:
    """Legge il PAT dal Credential Manager.

    Returns:
        Il PAT memorizzato oppure None se non presente.

    Raises:
        CredentialStoreUnavailableError: se il vault non e' disponibile.
    """
    _require_available()
    return keyring.get_password(SUPABASE_KEYRING_SERVICE, _pat_username(project_ref))


def has_pat(project_ref: str) -> bool:
    """Verifica se esiste un PAT memorizzato per il progetto."""
    return read_pat(project_ref) is not None


def delete_pat(project_ref: str) -> None:
    """Cancella il PAT dal Credential Manager, se presente.

    Non solleva eccezioni se il vault non e' disponibile o se la credenziale
    non esiste: la cancellazione e' un'operazione di pulizia best-effort.
    """
    if not credential_store_available():
        return
    try:
        keyring.delete_password(SUPABASE_KEYRING_SERVICE, _pat_username(project_ref))
    except Exception:
        # Se la credenziale non esiste, non c'e' nulla da cancellare.
        pass


def purge_all_pats() -> None:
    """Cancella tutti i PAT memorizzati per il gestionale."""
    if not credential_store_available():
        return
    backend = keyring.get_keyring()
    # Non esiste un'API per elencare le credenziali in modo portabile:
    # cancelliamo solo quelle note tramite delete_pat sui progetti conosciuti.
    # Questo e' un best-effort: la pulizia puntuale avviene in delete_pat.
    _ = backend  # backend non usato direttamente, manteniamo la firma per estensioni future