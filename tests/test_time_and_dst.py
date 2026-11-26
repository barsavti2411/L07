"""Tests for date parsing, midnight boundaries, and Asia/Jerusalem DST transitions."""

from __future__ import annotations

import pytest

import calendar_helpers as ch
import server
from tests.conftest import FakeCalendarService


def test_parse_iso_attaches_and_converts_timezones() -> None:
    naive = ch.parse_iso("2026-12-01T10:00:00")
    assert naive.isoformat() == "2026-12-01T10:00:00+02:00"
    utc = ch.parse_iso("2026-12-01T08:00:00Z")
    assert utc.isoformat() == "2026-12-01T10:00:00+02:00"
    ny = ch.parse_iso("2026-12-01T03:00:00-05:00")
    assert ny.isoformat() == "2026-12-01T10:00:00+02:00"


def test_parse_iso_handles_date_only_string() -> None:
    dt = ch.parse_iso("2026-12-01")
    assert dt.isoformat() == "2026-12-01T00:00:00+02:00"


def test_midnight_spanning_event_blocks_morning_without_leaking_prior_day(monkeypatch: pytest.MonkeyPatch) -> None:
    items = [
        {"start": {"dateTime": "2026-11-30T22:00:00+02:00"}, "end": {"dateTime": "2026-12-01T09:30:00+02:00"}},
        {"start": {"dateTime": "2026-11-30T23:00:00+02:00"}, "end": {"dateTime": "2026-12-01T00:00:00+02:00"}},
    ]
    monkeypatch.setattr(server, "get_calendar_service", lambda: FakeCalendarService(pages=[{"items": items}]))
    slots = server.find_free_slots("2026-12-01", duration_minutes=60)
    assert slots == [{"start": "2026-12-01T09:30:00+02:00", "end": "2026-12-01T20:00:00+02:00"}]


def test_dst_spring_forward_uses_utc_plus_3_in_asia_jerusalem(monkeypatch: pytest.MonkeyPatch) -> None:
    # Israel DST 2026 starts Friday 2026-03-27 at 02:00 (UTC+2 -> UTC+3)
    items = [{"start": {"dateTime": "2026-03-27T07:00:00Z"}, "end": {"dateTime": "2026-03-27T08:00:00Z"}}]
    monkeypatch.setattr(server, "get_calendar_service", lambda: FakeCalendarService(pages=[{"items": items}]))
    slots = server.find_free_slots("2026-03-27", duration_minutes=60)
    assert slots == [
        {"start": "2026-03-27T08:00:00+03:00", "end": "2026-03-27T10:00:00+03:00"},
        {"start": "2026-03-27T11:00:00+03:00", "end": "2026-03-27T20:00:00+03:00"},
    ]


def test_dst_fall_back_uses_utc_plus_2_in_asia_jerusalem(monkeypatch: pytest.MonkeyPatch) -> None:
    # Israel DST 2026 ends Sunday 2026-10-25 at 02:00 (UTC+3 -> UTC+2)
    items = [{"start": {"dateTime": "2026-10-25T08:00:00Z"}, "end": {"dateTime": "2026-10-25T09:00:00Z"}}]
    monkeypatch.setattr(server, "get_calendar_service", lambda: FakeCalendarService(pages=[{"items": items}]))
    slots = server.find_free_slots("2026-10-25", duration_minutes=60)
    assert slots == [
        {"start": "2026-10-25T08:00:00+02:00", "end": "2026-10-25T10:00:00+02:00"},
        {"start": "2026-10-25T11:00:00+02:00", "end": "2026-10-25T20:00:00+02:00"},
    ]


def test_event_busy_interval_ignores_missing_bounds() -> None:
    win_s, win_e = ch.parse_iso("2026-12-01T08:00:00+02:00"), ch.parse_iso("2026-12-01T20:00:00+02:00")
    assert ch.event_busy_interval({"start": {}, "end": {}}, win_s, win_e) is None
