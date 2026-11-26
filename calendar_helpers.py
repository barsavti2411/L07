"""Timezone, event-interval, and free-slot helpers for Asia/Jerusalem calendars."""

from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Jerusalem")


def parse_iso(value: str) -> datetime:
    """Parse an ISO 8601 date or timestamp and normalize it to Asia/Jerusalem."""
    dt = datetime.fromisoformat(value)
    return dt.replace(tzinfo=TZ) if dt.tzinfo is None else dt.astimezone(TZ)


def event_busy_interval(
    ev: dict[str, Any], win_start: datetime, win_end: datetime
) -> tuple[datetime, datetime] | None:
    """Return a clamped busy (start, end) pair in Asia/Jerusalem, or None if free."""
    if ev.get("status") == "cancelled" or ev.get("transparency") == "transparent":
        return None
    start_raw = ev.get("start", {}).get("dateTime") or ev.get("start", {}).get("date")
    end_raw = ev.get("end", {}).get("dateTime") or ev.get("end", {}).get("date")
    if not start_raw or not end_raw:
        return None
    b_start = max(parse_iso(start_raw), win_start)
    b_end = min(parse_iso(end_raw), win_end)
    return (b_start, b_end) if b_end > b_start else None


def compute_free_slots(
    items: list[dict[str, Any]], day_str: str, duration_minutes: int
) -> list[dict[str, str]]:
    """Compute available slots on YYYY-MM-DD between 08:00 and 20:00 Asia/Jerusalem."""
    day = datetime.strptime(day_str, "%Y-%m-%d").date()
    win_start = datetime.combine(day, time(8, 0), tzinfo=TZ)
    win_end = datetime.combine(day, time(20, 0), tzinfo=TZ)
    busy = sorted(
        interval
        for ev in items
        if (interval := event_busy_interval(ev, win_start, win_end)) is not None
    )
    cursor, needed, slots = win_start, timedelta(minutes=duration_minutes), []
    for b_start, b_end in busy:
        if b_start - cursor >= needed:
            slots.append({"start": cursor.isoformat(), "end": b_start.isoformat()})
        cursor = max(cursor, b_end)
    if win_end - cursor >= needed:
        slots.append({"start": cursor.isoformat(), "end": win_end.isoformat()})
    return slots
