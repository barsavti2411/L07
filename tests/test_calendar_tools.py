"""Tests for Calendar tools (list_events, create_event), validation, and API errors."""

from __future__ import annotations

from datetime import datetime, timedelta
from googleapiclient.errors import HttpError
import pytest

import server
from tests.conftest import FakeCalendarService, make_http_error


def test_list_events_formats_timed_all_day_and_untitled(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeCalendarService(
        pages=[
            {
                "items": [
                    {
                        "id": "e1",
                        "summary": "Volunteers schedule",
                        "start": {"dateTime": "2026-12-01T10:00:00+02:00"},
                        "end": {"dateTime": "2026-12-01T10:45:00+02:00"},
                        "description": "Topic",
                    },
                    {"id": "e2", "start": {"date": "2026-12-02"}, "end": {"date": "2026-12-03"}},
                ]
            }
        ]
    )
    monkeypatch.setattr(server, "get_calendar_service", lambda: fake)
    events = server.list_events(days_ahead=14)
    assert events == [
        {
            "id": "e1",
            "title": "Volunteers schedule",
            "start": "2026-12-01T10:00:00+02:00",
            "end": "2026-12-01T10:45:00+02:00",
            "description": "Topic",
        },
        {"id": "e2", "title": "(No title)", "start": "2026-12-02", "end": "2026-12-03", "description": ""},
    ]
    call = fake.list_calls[0]
    assert call["calendarId"] == "primary" and call["singleEvents"] is True and call["orderBy"] == "startTime"


@pytest.mark.parametrize(("days_ahead", "expected_days"), [(0, 1), (-3, 1), (120, 90)])
def test_list_events_clamps_days_ahead(monkeypatch: pytest.MonkeyPatch, days_ahead: int, expected_days: int) -> None:
    fake = FakeCalendarService()
    monkeypatch.setattr(server, "get_calendar_service", lambda: fake)
    server.list_events(days_ahead=days_ahead)
    call = fake.list_calls[0]
    delta = datetime.fromisoformat(call["timeMax"]) - datetime.fromisoformat(call["timeMin"])
    assert delta == timedelta(days=expected_days)


def test_create_event_normalizes_to_asia_jerusalem(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeCalendarService(
        insert_result={
            "id": "ev-42",
            "summary": "Sync",
            "start": {"dateTime": "2026-12-01T10:00:00+02:00"},
            "end": {"dateTime": "2026-12-01T10:45:00+02:00"},
            "htmlLink": "https://calendar.google.com/event?eid=42",
        }
    )
    monkeypatch.setattr(server, "get_calendar_service", lambda: fake)
    res = server.create_event("Sync", "2026-12-01T08:00:00Z", "2026-12-01T08:45:00Z", "Notes")
    assert res["event_id"] == "ev-42"
    body = fake.insert_calls[0]["body"]
    assert body["start"] == {"dateTime": "2026-12-01T10:00:00+02:00", "timeZone": "Asia/Jerusalem"}
    assert body["end"] == {"dateTime": "2026-12-01T10:45:00+02:00", "timeZone": "Asia/Jerusalem"}
    assert not fake.delete_called


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("2026-12-01T10:00:00+02:00", "2026-12-01T10:00:00+02:00"),
        ("2026-12-01T11:00:00+02:00", "2026-12-01T10:00:00+02:00"),
    ],
)
def test_create_event_rejects_end_not_after_start(monkeypatch: pytest.MonkeyPatch, start: str, end: str) -> None:
    fake = FakeCalendarService()
    monkeypatch.setattr(server, "get_calendar_service", lambda: fake)
    with pytest.raises(ValueError, match="end must be after start"):
        server.create_event("Invalid", start, end)
    assert fake.insert_calls == []


def test_create_event_rejects_malformed_iso_timestamp(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeCalendarService()
    monkeypatch.setattr(server, "get_calendar_service", lambda: fake)
    with pytest.raises(ValueError):
        server.create_event("Bad", "not-a-date", "2026-12-01T10:00:00+02:00")
    assert fake.insert_calls == []


def test_create_event_server_does_not_deduplicate_without_coordinator_check(monkeypatch: pytest.MonkeyPatch) -> None:
    existing = {
        "id": "dup-1",
        "summary": "Volunteers schedule",
        "start": {"dateTime": "2026-12-01T10:00:00+02:00"},
        "end": {"dateTime": "2026-12-01T10:45:00+02:00"},
    }
    fake = FakeCalendarService(pages=[{"items": [existing]}])
    monkeypatch.setattr(server, "get_calendar_service", lambda: fake)
    events = server.list_events(days_ahead=14)
    has_conflict = any(
        ev["start"] < "2026-12-01T10:45:00+02:00" and ev["end"] > "2026-12-01T10:00:00+02:00"
        for ev in events
    )
    assert has_conflict is True
    assert fake.insert_calls == []


@pytest.mark.parametrize("status", [403, 500])
def test_calendar_tools_propagate_http_errors(monkeypatch: pytest.MonkeyPatch, status: int) -> None:
    fake = FakeCalendarService(error=make_http_error(status, "insufficientPermissions"))
    monkeypatch.setattr(server, "get_calendar_service", lambda: fake)
    with pytest.raises(HttpError):
        server.list_events()
    with pytest.raises(HttpError):
        server.find_free_slots("2026-12-01", 30)
    with pytest.raises(HttpError):
        server.create_event("Test", "2026-12-01T10:00:00+02:00", "2026-12-01T11:00:00+02:00")
