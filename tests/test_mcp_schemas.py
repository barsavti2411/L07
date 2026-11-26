"""Tests for MCP tool registration, parameter schemas, and security boundaries."""

from __future__ import annotations

import pytest

import server

EXPECTED_TOOLS = {
    "search_emails",
    "read_email",
    "create_draft",
    "list_events",
    "find_free_slots",
    "create_event",
}


def _tools_by_name() -> dict[str, object]:
    return {t.name: t for t in server.mcp._tool_manager.list_tools()}


def test_mcp_server_name_is_gmail_calendar() -> None:
    assert server.mcp.name == "gmail-calendar"


def test_exactly_six_expected_tools_registered() -> None:
    tools = _tools_by_name()
    assert len(tools) == 6
    assert set(tools) == EXPECTED_TOOLS


@pytest.mark.parametrize(
    "forbidden",
    [
        "send_email",
        "send_draft",
        "forward_email",
        "delete_email",
        "delete_event",
        "update_event",
        "patch_event",
    ],
)
def test_forbidden_send_forward_and_delete_tools_absent(forbidden: str) -> None:
    tools = _tools_by_name()
    assert forbidden not in tools


def test_tool_descriptions_document_safety_and_timezone() -> None:
    tools = _tools_by_name()
    assert "without sending" in tools["create_draft"].description.lower()
    assert "untrusted" in tools["read_email"].description.lower()
    assert "Asia/Jerusalem" in tools["list_events"].description
    assert "Asia/Jerusalem" in tools["find_free_slots"].description
    assert "Asia/Jerusalem" in tools["create_event"].description


@pytest.mark.parametrize(
    ("tool_name", "expected_required", "expected_props"),
    [
        ("search_emails", {"query"}, {"query", "max_results"}),
        ("read_email", {"message_id"}, {"message_id"}),
        ("create_draft", {"to", "subject", "body"}, {"to", "subject", "body"}),
        ("list_events", set(), {"days_ahead"}),
        ("find_free_slots", {"date"}, {"date", "duration_minutes"}),
        ("create_event", {"title", "start", "end"}, {"title", "start", "end", "description"}),
    ],
)
def test_tool_input_schemas_and_required_fields(
    tool_name: str, expected_required: set[str], expected_props: set[str]
) -> None:
    schema = _tools_by_name()[tool_name].parameters
    assert set(schema.get("required", [])) == expected_required
    assert set(schema.get("properties", {}).keys()) == expected_props


def test_tool_default_values_in_schemas() -> None:
    tools = _tools_by_name()
    assert tools["search_emails"].parameters["properties"]["max_results"]["default"] == 10
    assert tools["list_events"].parameters["properties"]["days_ahead"]["default"] == 7
    assert tools["find_free_slots"].parameters["properties"]["duration_minutes"]["default"] == 30
    assert tools["create_event"].parameters["properties"]["description"]["default"] == ""
