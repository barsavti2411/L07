"""Tests for OAuth configuration, credential refresh, and secret protection."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import pytest

import google_auth

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_get_private_dir_unset_or_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("GOOGLE_PRIVATE_DIR", raising=False)
    with pytest.raises(RuntimeError, match="GOOGLE_PRIVATE_DIR"):
        google_auth.get_private_dir()

    missing = tmp_path / "does_not_exist_secret_dir"
    monkeypatch.setenv("GOOGLE_PRIVATE_DIR", str(missing))
    with pytest.raises(FileNotFoundError) as exc_info:
        google_auth.get_private_dir()
    assert str(missing) not in str(exc_info.value)


def test_load_credentials_missing_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOOGLE_PRIVATE_DIR", str(tmp_path))
    with pytest.raises(FileNotFoundError, match="credentials.json"):
        google_auth.load_credentials()

    (tmp_path / "credentials.json").write_text("{}", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="token.json"):
        google_auth.load_credentials()


def test_load_credentials_valid_token_does_not_refresh(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "credentials.json").write_text("{}", encoding="utf-8")
    (tmp_path / "token.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("GOOGLE_PRIVATE_DIR", str(tmp_path))

    refreshed = False

    class FakeCreds:
        valid = True
        expired = False
        refresh_token = "r1"

        def refresh(self, _req: object) -> None:
            nonlocal refreshed
            refreshed = True

    monkeypatch.setattr(google_auth.Credentials, "from_authorized_user_file", staticmethod(lambda _p: FakeCreds()))
    creds = google_auth.load_credentials()
    assert creds.valid is True
    assert refreshed is False


def test_load_credentials_refreshes_and_saves_expired_token(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "credentials.json").write_text("{}", encoding="utf-8")
    token_file = tmp_path / "token.json"
    token_file.write_text('{"token":"old"}', encoding="utf-8")
    monkeypatch.setenv("GOOGLE_PRIVATE_DIR", str(tmp_path))

    class FakeCreds:
        valid = False
        expired = True
        refresh_token = "rt"

        def refresh(self, _req: object) -> None:
            self.valid = True

        def to_json(self) -> str:
            return '{"token":"new"}'

    monkeypatch.setattr(google_auth.Credentials, "from_authorized_user_file", staticmethod(lambda _p: FakeCreds()))
    creds = google_auth.load_credentials()
    assert creds.valid is True
    assert token_file.read_text(encoding="utf-8") == '{"token":"new"}'


def test_load_credentials_rejects_unrefreshable_token(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "credentials.json").write_text("{}", encoding="utf-8")
    (tmp_path / "token.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("GOOGLE_PRIVATE_DIR", str(tmp_path))

    class BadCreds:
        valid = False
        expired = True
        refresh_token = None

    monkeypatch.setattr(google_auth.Credentials, "from_authorized_user_file", staticmethod(lambda _p: BadCreds()))
    with pytest.raises(RuntimeError, match="without interactive login"):
        google_auth.load_credentials()


def test_service_builders_disable_discovery_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, bool]] = []
    monkeypatch.setattr(google_auth, "load_credentials", lambda: SimpleNamespace())
    monkeypatch.setattr(
        google_auth,
        "build",
        lambda name, ver, credentials, cache_discovery: calls.append((name, ver, cache_discovery)) or name,
    )
    assert google_auth.get_gmail_service() == "gmail"
    assert google_auth.get_calendar_service() == "calendar"
    assert calls == [("gmail", "v1", False), ("calendar", "v3", False)]


def test_gitignore_excludes_secrets_and_local_configs() -> None:
    gi = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in ["credentials.json", "token.json", ".env", ".venv/", ".meetbridge/", "mcp_config*.json"]:
        assert pattern in gi


def test_source_files_contain_no_hardcoded_secrets() -> None:
    for rel in ["server.py", "calendar_helpers.py", "google_auth.py"]:
        text = (PROJECT_ROOT / rel).read_text(encoding="utf-8")
        assert "AIza" not in text and "GOCSPX-" not in text and "ya29." not in text
