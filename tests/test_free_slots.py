"""Tests for find_free_slots using events.list, conflict handling, and all-day events."""

from __future__ import annotations

import pytest

import server
from tests.conftest import FakeCalendarService


def _ev(start: str, end: str, *, all_day: bool = False, transparency: str | None = None, status: str = "confirmed") -> dict:
    key = "date" if all_day else "dateTime"
    item: dict = {"status": status, "start": {key: start}, "end": {key: end}}
    if transparency is not None:
        item["transparency"] = transparency
    return item


@pytest.mark.parametrize("duration", [4, 0, -10, 721])
def test_find_free_slots_rejects_invalid_duration(duration: int) -> None:
    with pytest.raises(ValueError, match="duration_minutes"):
        server.find_free_slots("2026-12-01", duration_minutes=duration)


def test_find_free_slots_rejects_invalid_date_format() -> None:
    with pytest.raises(ValueError):
        server.find_free_slots("01-12-2026", duration_minutes=30)


def test_find_free_slots_uses_events_list_not_freebusy(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeCalendarService(pages=[{"items": []}])
    monkeypatch.setattr(server, "get_calendar_service", lambda: fake)
    slots = server.find_free_slots("2026-12-01", duration_minutes=60)
    assert not fake.freebusy_called
    assert len(fake.list_calls) == 1
    assert fake.list_calls[0]["singleEvents"] is True
    assert slots == [{"start": "2026-12-01T08:00:00+02:00", "end": "2026-12-01T20:00:00+02:00"}]


def test_find_free_slots_filters_gaps_smaller_than_duration(monkeypatch: pytest.MonkeyPatch) -> None:
    items = [_ev("2026-12-01T08:30:00+02:00", "2026-12-01T19:30:00+02:00")]
    monkeypatch.setattr(server, "get_calendar_service", lambda: FakeCalendarService(pages=[{"items": items}]))
    assert server.find_free_slots("2026-12-01", duration_minutes=45) == []
    assert len(server.find_free_slots("2026-12-01", duration_minutes=30)) == 2


def test_find_free_slots_handles_overlapping_nested_and_adjacent_events(monkeypatch: pytest.MonkeyPatch) -> None:
    items = [
        _ev("2026-12-01T09:00:00+02:00", "2026-12-01T11:00:00+02:00"),
        _ev("2026-12-01T09:30:00+02:00", "2026-12-01T10:30:00+02:00"),
        _ev("2026-12-01T10:30:00+02:00", "2026-12-01T12:00:00+02:00"),
        _ev("2026-12-01T12:00:00+02:00", "2026-12-01T13:00:00+02:00"),
    ]
    monkeypatch.setattr(server, "get_calendar_service", lambda: FakeCalendarService(pages=[{"items": items}]))
    slots = server.find_free_slots("2026-12-01", duration_minutes=45)
    assert slots == [
        {"start": "2026-12-01T08:00:00+02:00", "end": "2026-12-01T09:00:00+02:00"},
        {"start": "2026-12-01T13:00:00+02:00", "end": "2026-12-01T20:00:00+02:00"},
    ]


def test_find_free_slots_clamps_window_edges_and_ignores_outside_events(monkeypatch: pytest.MonkeyPatch) -> None:
    items = [
        _ev("2026-12-01T07:00:00+02:00", "2026-12-01T09:00:00+02:00"),
        _ev("2026-12-01T19:15:00+02:00", "2026-12-01T21:00:00+02:00"),
        _ev("2026-12-01T22:00:00+02:00", "2026-12-01T23:00:00+02:00"),
    ]
    monkeypatch.setattr(server, "get_calendar_service", lambda: FakeCalendarService(pages=[{"items": items}]))
    assert server.find_free_slots("2026-12-01", duration_minutes=60) == [
        {"start": "2026-12-01T09:00:00+02:00", "end": "2026-12-01T19:15:00+02:00"}
    ]


def test_find_free_slots_all_day_opaque_blocks_and_transparent_allows(monkeypatch: pytest.MonkeyPatch) -> None:
    opaque = [_ev("2026-12-01", "2026-12-02", all_day=True)]
    monkeypatch.setattr(server, "get_calendar_service", lambda: FakeCalendarService(pages=[{"items": opaque}]))
    assert server.find_free_slots("2026-12-01", duration_minutes=30) == []

    free_all_day = [
        _ev("2026-12-01", "2026-12-02", all_day=True, transparency="transparent"),
        _ev("2026-12-01T10:00:00+02:00", "2026-12-01T11:00:00+02:00", status="cancelled"),
    ]
    monkeypatch.setattr(server, "get_calendar_service", lambda: FakeCalendarService(pages=[{"items": free_all_day}]))
    assert server.find_free_slots("2026-12-01", duration_minutes=30) == [
        {"start": "2026-12-01T08:00:00+02:00", "end": "2026-12-01T20:00:00+02:00"}
    ]


def test_find_free_slots_handles_pagination(monkeypatch: pytest.MonkeyPatch) -> None:
    pages = [
        {"items": [_ev("2026-12-01T09:00:00+02:00", "2026-12-01T10:00:00+02:00")], "nextPageToken": "p2"},
        {"items": [_ev("2026-12-01T14:00:00+02:00", "2026-12-01T15:00:00+02:00")]},
    ]
    fake = FakeCalendarService(pages=pages)
    monkeypatch.setattr(server, "get_calendar_service", lambda: fake)
    slots = server.find_free_slots("2026-12-01", duration_minutes=60)
    assert len(fake.list_calls) == 2 and fake.list_calls[1]["pageToken"] == "p2"
    assert len(slots) == 3


def test_conflict_scenario_yields_alternatives_between_09_and_17(monkeypatch: pytest.MonkeyPatch) -> None:
    items = [_ev("2026-12-01T10:00:00+02:00", "2026-12-01T10:45:00+02:00")]
    monkeypatch.setattr(server, "get_calendar_service", lambda: FakeCalendarService(pages=[{"items": items}]))
    slots = server.find_free_slots("2026-12-01", duration_minutes=45)
    assert slots == [
        {"start": "2026-12-01T08:00:00+02:00", "end": "2026-12-01T10:00:00+02:00"},
        {"start": "2026-12-01T10:45:00+02:00", "end": "2026-12-01T20:00:00+02:00"},
    ]
    assert all(not (s["start"] <= "2026-12-01T10:00:00+02:00" and s["end"] >= "2026-12-01T10:45:00+02:00") for s in slots)
