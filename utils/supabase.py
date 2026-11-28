"""Utility per la configurazione e il collegamento Supabase del gestionale Barber."""

from urllib.parse import urlparse


def extract_project_ref(project_url: str) -> str | None:
    """Estrae il Project Reference ID dalla Project URL.

    Accetta URL del tipo ``https://<project-ref>.supabase.co`` (con o senza
    protocollo) e restituisce il Project Reference ID.

    Args:
        project_url: Project URL inserita dall'utente (es. ``https://xxxxx.supabase.co``).

    Returns:
        Il Project Reference ID estratto, oppure ``None`` se la URL non e'
        valorizzata o non contiene un riferimento.
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
