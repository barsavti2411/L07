"""Local Google OAuth credential loading and API service builders."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build

logger = logging.getLogger("gmail-calendar.auth")


def get_private_dir() -> Path:
    """Return the validated private credentials directory from GOOGLE_PRIVATE_DIR."""
    raw_dir = os.environ.get("GOOGLE_PRIVATE_DIR", "").strip()
    if not raw_dir:
        raise RuntimeError(
            "GOOGLE_PRIVATE_DIR environment variable is not set."
        )
    private_dir = Path(raw_dir)
    if not private_dir.is_dir():
        raise FileNotFoundError(
            "GOOGLE_PRIVATE_DIR does not point to an existing directory."
        )
    return private_dir


def load_credentials() -> Credentials:
    """Load OAuth credentials from token.json and refresh silently if needed."""
    private_dir = get_private_dir()
    credentials_path = private_dir / "credentials.json"
    token_path = private_dir / "token.json"

    if not credentials_path.is_file():
        raise FileNotFoundError("credentials.json not found in GOOGLE_PRIVATE_DIR.")
    if not token_path.is_file():
        raise FileNotFoundError("token.json not found in GOOGLE_PRIVATE_DIR.")

    creds = Credentials.from_authorized_user_file(str(token_path))
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            logger.info("Refreshing expired Google OAuth access token.")
            creds.refresh(Request())
            token_path.write_text(creds.to_json(), encoding="utf-8")
        else:
            raise RuntimeError(
                "OAuth token is invalid and cannot be refreshed without interactive login."
            )
    return creds


def get_gmail_service() -> Resource:
    """Build and return an authenticated Gmail API v1 client."""
    return build("gmail", "v1", credentials=load_credentials(), cache_discovery=False)


def get_calendar_service() -> Resource:
    """Build and return an authenticated Google Calendar API v3 client."""
    return build("calendar", "v3", credentials=load_credentials(), cache_discovery=False)
