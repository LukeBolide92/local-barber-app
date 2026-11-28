from utils.supabase import extract_project_ref, mask_token, redact_secrets


class TestExtractProjectRef:
    def test_empty_url_returns_none(self):
        assert extract_project_ref("") is None
        assert extract_project_ref(None) is None

    def test_extracts_ref_from_url(self):
        assert extract_project_ref("https://abc123xyz.supabase.co") == "abc123xyz"

    def test_extracts_ref_without_scheme(self):
        assert extract_project_ref("abc123xyz.supabase.co") == "abc123xyz"

    def test_extracts_ref_with_path(self):
        assert extract_project_ref("https://abc123xyz.supabase.co/dashboard") == "abc123xyz"

    def test_strips_whitespace(self):
        assert extract_project_ref("  https://abc123xyz.supabase.co  ") == "abc123xyz"


class TestRedactionHelpers:
    def test_redact_removes_secret(self):
        text = "errore con token supabase=abc123xyz"
        cleaned = redact_secrets(text, "abc123xyz")
        assert "abc123xyz" not in cleaned
        assert "***" in cleaned

    def test_redact_without_secrets_is_unchanged(self):
        assert redact_secrets("nessun segreto", "") == "nessun segreto"

    def test_redact_multiple_secrets(self):
        cleaned = redact_secrets("token=aaa pass=bbb", "aaa", "bbb")
        assert "aaa" not in cleaned
        assert "bbb" not in cleaned

    def test_mask_token_hides_most_characters(self):
        token = "abcdef1234567890"
        masked = mask_token(token)
        assert token not in masked
        assert masked == "****7890"

    def test_mask_token_empty(self):
        assert mask_token("") == ""
