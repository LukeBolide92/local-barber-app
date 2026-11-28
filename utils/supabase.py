"""Utility per la configurazione e il collegamento Supabase del gestionale Private Barber Manager."""

import re
from typing import Optional

from urllib.parse import urlparse

_REDACTED = "***"


def extract_project_ref(project_url: str) -> Optional[str]:
    """Estrai il Project Reference ID dalla Project URL.

    Accetta URL del tipo ``https://<project-ref>.supabase.co`` (con o senza
    protocollo) e restituisce il Project Reference ID.

    Args:
        project_url: Project URL inserita dall'utente (es. ``https://xxxxx.supabase.co``).

    Returns:
        Il Project Reference ID estratto, oppure ``None`` se la URL non è valida o non contiene un riferimento.
    """
    url = (project_url or "").strip()
    if not url:
        return None
    parsed = urlparse(url if "//" in url else f"https://{url}")
    hostname = parsed.hostname or ""
    if not hostname:
        return None
    ref = hostname.split(".")[0].strip()
    return ref or None


def redact_secrets(text: str, *secrets: str) -> str:
    """Sostituisce ogni occorrenza di una stringa segreta in ``text`` con ``REDACTED``.

    Args:
        text: testo da pulire.
        *secrets: stringhe da mascherare.

    Returns:
        testo con le segreti sostituite.
    """
    result = text
    for secret in secrets:
        if secret:
            result = result.replace(secret, _REDACTED)
    return result


def mask_token(token: str) -> str:
    """Mostra solo l'ultimo 4 caratteri di un token di accesso.

    Args:
        token: PAT o qualsiasi token.

    Returns:
        Token mostrato in modo parzialmente mascherato.
    """
    if not token:
        return ""
    visible = min(4, len(token))
    if visible == len(token):
        return token
    return "****" + token[-visible:]
