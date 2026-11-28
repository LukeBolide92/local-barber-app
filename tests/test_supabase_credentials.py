import pytest
from keyring.backends import fail
from services.supabase_credential_service import (
    CredentialStoreUnavailableError,
    SUPABASE_KEYRING_SERVICE,
    credential_store_available,
    delete_pat,
    has_pat,
    read_pat,
    store_pat,
)

# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------
class FakeKeyringBackend:
    def __init__(self):
        self._store = {}
    def set_password(self, service, username, password):
        self._store[(service, username)] = password
    def get_password(self, service, username):
        return self._store.get((service, username))
    def delete_password(self, service, username):
        self._store.pop((service, username), None)

@pytest.fixture
def fake_keyring(monkeypatch):
    backend = FakeKeyringBackend()
    import services.supabase_credential_service as mod
    monkeypatch.setattr(mod.keyring, "get_keyring", lambda: backend)
    monkeypatch.setattr(mod.keyring, "set_password", backend.set_password)
    monkeypatch.setattr(mod.keyring, "get_password", backend.get_password)
    monkeypatch.setattr(mod.keyring, "delete_password", backend.delete_password)
    return backend

# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------
def test_credential_store_available_when_keyring_works(fake_keyring):
    assert credential_store_available() is True

def test_credential_store_unavailable_when_keyring_none(monkeypatch):
    import services.supabase_credential_service as mod
    monkeypatch.setattr(mod.keyring, "get_keyring", lambda: None)
    assert credential_store_available() is False

def test_credential_store_unavailable_when_keyring_fail(monkeypatch):
    import services.supabase_credential_service as mod
    monkeypatch.setattr(mod.keyring, "get_keyring", lambda: fail.Keyring())
    assert credential_store_available() is False

def test_store_and_read_pat_roundtrip(fake_keyring):
    store_pat("project-123", "my-secret-pat")
    assert read_pat("project-123") == "my-secret-pat"

def test_read_missing_pat_returns_none(fake_keyring):
    assert read_pat("nonexistent") is None

def test_delete_pat_removes_pat(fake_keyring):
    store_pat("project-123", "pw")
    delete_pat("project-123")
    assert read_pat("project-123") is None

def test_has_pat_returns_true_when_present(fake_keyring):
    store_pat("project-123", "pw")
    assert has_pat("project-123") is True

def test_has_pat_returns_false_when_missing(fake_keyring):
    assert has_pat("missing") is False

def test_store_pat_raises_when_keyring_unavailable(monkeypatch):
    import services.supabase_credential_service as mod
    monkeypatch.setattr(mod.keyring, "get_keyring", lambda: None)
    with pytest.raises(CredentialStoreUnavailableError):
        store_pat("project-123", "secret")