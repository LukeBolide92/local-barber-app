from utils.supabase import extract_project_ref


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
