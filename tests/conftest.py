"""Shared fake Google API builders and helpers for mocked pytest suites."""

from __future__ import annotations

import base64
import json
from typing import Any

from googleapiclient.errors import HttpError
import httplib2


def b64(text: str) -> str:
    """Encode UTF-8 text as unpadded/padded URL-safe base64 for Gmail payloads."""
    return base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii")


def make_http_error(status: int, reason: str, message: str = "API error") -> HttpError:
    """Create a realistic googleapiclient HttpError for mocked API failure tests."""
    resp = httplib2.Response({"status": str(status), "reason": reason})
    body = json.dumps({"error": {"code": status, "message": message, "errors": [{"reason": reason}]}}).encode("utf-8")
    return HttpError(resp=resp, content=body, uri="https://www.googleapis.com/test")


class _Exec:
    """Minimal Google API executable request wrapper."""

    def __init__(self, result: Any = None, error: Exception | None = None) -> None:
        self._result = result
        self._error = error

    def execute(self) -> Any:
        if self._error is not None:
            raise self._error
        return self._result


class FakeGmailService:
    """Mocked Gmail API v1 client recording calls and returning preset responses."""

    def __init__(
        self,
        list_result: dict[str, Any] | None = None,
        messages: dict[str, dict[str, Any]] | None = None,
        draft_result: dict[str, Any] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.list_result = list_result or {"messages": []}
        self._messages = messages or {}
        self.draft_result = draft_result or {"id": "d1", "message": {"id": "m1"}}
        self.error = error
        self.list_calls: list[dict[str, Any]] = []
        self.get_calls: list[dict[str, Any]] = []
        self.draft_calls: list[dict[str, Any]] = []
        self.send_called = False

    def users(self) -> FakeGmailService:
        return self

    def messages(self) -> _FakeMessages:
        return _FakeMessages(self)

    def drafts(self) -> _FakeDrafts:
        return _FakeDrafts(self)


class _FakeMessages:
    def __init__(self, root: FakeGmailService) -> None:
        self._root = root

    def list(self, **kwargs: Any) -> _Exec:
        self._root.list_calls.append(kwargs)
        return _Exec(self._root.list_result, self._root.error)

    def get(self, **kwargs: Any) -> _Exec:
        self._root.get_calls.append(kwargs)
        return _Exec(self._root._messages.get(kwargs["id"], {}), self._root.error)

    def send(self, **kwargs: Any) -> _Exec:
        self._root.send_called = True
        return _Exec({}, AssertionError("send() must never be called"))


class _FakeDrafts:
    def __init__(self, root: FakeGmailService) -> None:
        self._root = root

    def create(self, **kwargs: Any) -> _Exec:
        self._root.draft_calls.append(kwargs)
        return _Exec(self._root.draft_result, self._root.error)


class FakeCalendarService:
    """Mocked Google Calendar API v3 client supporting paginated list and insert."""

    def __init__(
        self,
        pages: list[dict[str, Any]] | None = None,
        insert_result: dict[str, Any] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.pages = pages or [{"items": []}]
        self.insert_result = insert_result or {"id": "ev1", "summary": "Test", "start": {}, "end": {}, "htmlLink": ""}
        self.error = error
        self.list_calls: list[dict[str, Any]] = []
        self.insert_calls: list[dict[str, Any]] = []
        self.freebusy_called = False
        self.delete_called = False

    def events(self) -> _FakeEvents:
        return _FakeEvents(self)

    def freebusy(self) -> _FakeFreeBusy:
        self.freebusy_called = True
        raise AssertionError("freebusy() must not be called")


class _FakeEvents:
    def __init__(self, root: FakeCalendarService) -> None:
        self._root = root

    def list(self, **kwargs: Any) -> _Exec:
        self._root.list_calls.append(kwargs)
        idx = len(self._root.list_calls) - 1
        page = self._root.pages[min(idx, len(self._root.pages) - 1)]
        return _Exec(page, self._root.error)

    def insert(self, **kwargs: Any) -> _Exec:
        self._root.insert_calls.append(kwargs)
        return _Exec(self._root.insert_result, self._root.error)

    def delete(self, **kwargs: Any) -> _Exec:
        self._root.delete_called = True
        return _Exec({}, AssertionError("delete() must never be called"))


class _FakeFreeBusy:
    def query(self, **kwargs: Any) -> _Exec:
        raise AssertionError("freebusy().query() must not be called")
