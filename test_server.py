"""Real stdio MCP client integration test for the gmail-calendar server."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import sys
from typing import Any
from zoneinfo import ZoneInfo

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_DIR = Path(__file__).resolve().parent
EXPECTED_TOOLS = {
    "search_emails",
    "read_email",
    "create_draft",
    "list_events",
    "find_free_slots",
    "create_event",
}


def _extract_events(call_result: Any) -> list[dict[str, Any]]:
    """Extract event dictionaries from structuredContent or TextContent blocks."""
    structured = getattr(call_result, "structuredContent", None)
    if isinstance(structured, dict) and isinstance(structured.get("result"), list):
        return [item for item in structured["result"] if isinstance(item, dict)]

    events: list[dict[str, Any]] = []
    for block in call_result.content:
        text = getattr(block, "text", "").strip()
        if not text:
            continue
        parsed = json.loads(text)
        if isinstance(parsed, list):
            events.extend(item for item in parsed if isinstance(item, dict))
        elif isinstance(parsed, dict):
            events.append(parsed)
    return events


async def run_test() -> int:
    """Launch gmail-calendar over uv/stdio, verify 6 tools, and call list_events."""
    env = os.environ.copy()
    env.setdefault("GOOGLE_PRIVATE_DIR", r"C:\Users\User\.meetbridge")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "--no-sync", "python", "-B", "server.py"],
        env=env,
        cwd=str(PROJECT_DIR),
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            init_result = await asyncio.wait_for(session.initialize(), timeout=15.0)
            print(f"MCP initialized: {init_result.serverInfo.name}")

            tools_result = await asyncio.wait_for(session.list_tools(), timeout=10.0)
            tool_names = [tool.name for tool in tools_result.tools]
            print(f"tools/list count: {len(tool_names)}")
            print(f"tools/list names: {tool_names}")

            if len(tool_names) != 6 or set(tool_names) != EXPECTED_TOOLS:
                print(f"ERROR: Expected {sorted(EXPECTED_TOOLS)}, got {sorted(tool_names)}")
                return 1

            call_result = await session.call_tool(
                "list_events",
                arguments={"days_ahead": 1},
                read_timeout_seconds=timedelta(seconds=20),
            )
            if call_result.isError:
                texts = [getattr(c, "text", str(c)) for c in call_result.content]
                print(f"tools/call list_events FAILED (isError=True): {' | '.join(texts)}")
                return 1

            events = _extract_events(call_result)
            print(f"tools/call list_events SUCCEEDED: {len(events)} event(s) in next 1 day.")
            for ev in events:
                print(f"  - {ev.get('start', '')} -> {ev.get('title', '')}")

            tomorrow = (datetime.now(ZoneInfo("Asia/Jerusalem")).date() + timedelta(days=1)).isoformat()
            free_result = await session.call_tool(
                "find_free_slots",
                arguments={"date": tomorrow, "duration_minutes": 60},
                read_timeout_seconds=timedelta(seconds=20),
            )
            if free_result.isError:
                texts = [getattr(c, "text", str(c)) for c in free_result.content]
                print(f"tools/call find_free_slots FAILED (isError=True): {' | '.join(texts)}")
                return 1

            slots = _extract_events(free_result)
            print(f"tools/call find_free_slots SUCCEEDED for {tomorrow}: {len(slots)} slot(s).")
            for slot in slots:
                print(f"  - {slot.get('start', '')} -> {slot.get('end', '')}")
            return 0


def main() -> int:
    """Run the async MCP test with an overall bounded timeout."""
    try:
        return asyncio.run(asyncio.wait_for(run_test(), timeout=35.0))
    except TimeoutError:
        print("ERROR: MCP integration test timed out after 35s.")
        return 1
    except Exception as exc:
        print(f"ERROR: MCP integration test failed: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
