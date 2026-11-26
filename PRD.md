# Product Requirements Document (PRD) — L07 `gmail-calendar` MCP Server

## 1. Objectives & Scope

The `gmail-calendar` MCP server enables an AI assistant (Antigravity) to assist with email triage and calendar coordination on a dedicated Google account while enforcing strict safety and privacy boundaries at the server layer.

### In Scope
- Local Python MCP server (`FastMCP`, `stdio` transport) exposing exactly six tools for Gmail and Google Calendar.
- External OAuth 2.0 credential loading from `GOOGLE_PRIVATE_DIR` without interactive browser flows.
- `Asia/Jerusalem` time-zone normalization, DST-aware slot calculation, and conflict/all-day handling.
- Automated mocked `pytest` suite (65 tests) and live `stdio` MCP integration verification (`test_server.py`).

### Out of Scope
- Sending, forwarding, or deleting emails.
- Deleting, patching, or updating existing calendar events.
- Interactive browser OAuth flows or credential storage inside the repository.
- Server-side automatic deduplication of `create_event` calls (handled by coordinator workflow before insertion).

## 2. Functional Requirements

| ID | Requirement | Status |
| :--- | :--- | :--- |
| **FR-1** | `search_emails(query, max_results=10)` searches Gmail and returns sender, recipient, subject, date, snippet, and ID, clamping `max_results` to `[1, 50]`. | Verified (Mocked + Live) |
| **FR-2** | `read_email(message_id)` extracts headers and plain-text body (recursing nested MIME parts) and appends an untrusted-data `security_note`. | Verified (Mocked + Live) |
| **FR-3** | `create_draft(to, subject, body)` creates an RFC-2822 Gmail draft without sending it and returns `status="draft_created"`. | Verified (Mocked + Live) |
| **FR-4** | `list_events(days_ahead=7)` lists upcoming primary calendar events in `Asia/Jerusalem`, clamping `days_ahead` to `[1, 90]`. | Verified (Mocked + Live) |
| **FR-5** | `find_free_slots(date, duration_minutes=30)` computes open windows between `08:00` and `20:00` `Asia/Jerusalem` using paginated `events.list` (avoiding `freeBusy` 403), handling busy, all-day, `transparent`, cancelled, overlapping, and DST events. | Verified (Mocked + Live) |
| **FR-6** | `create_event(title, start, end, description="")` validates `end > start`, normalizes timestamps to `Asia/Jerusalem`, and inserts a primary calendar event. | Verified (Mocked + Live) |

## 3. Security & Non-Functional Requirements

- **SEC-1 (Least-Privilege Tools):** No email send/forward/delete tools and no calendar delete/update tools may be registered.
- **SEC-2 (Untrusted Content Marking):** `read_email` explicitly marks email bodies as untrusted data to reduce indirect prompt-injection risk at the coordinator layer.
- **SEC-3 (Credential Isolation):** `credentials.json` and `token.json` must live outside the project in `GOOGLE_PRIVATE_DIR`; error messages must not leak filesystem paths or secret values; `.gitignore` must exclude secrets, `.env`, `.venv/`, and local MCP configs.
- **NFR-1 (Protocol Hygiene):** Logging must go exclusively to `stderr` so `stdout` remains clean for MCP JSON-RPC frames.
- **NFR-2 (Modularity):** Every project `.py` file must contain fewer than 150 lines.

## 4. Acceptance Criteria & Verification Separation

| Verification Layer | What It Proves | Evidence |
| :--- | :--- | :--- |
| **Mocked Unit & Schema Tests (`pytest`)** | Deterministic server behavior: 6-tool registration, absence of forbidden tools, parsing, validation, slot math, DST, `HttpError` propagation, and `google_auth` error handling. Does **not** prove live Google API behavior or LLM security. | `uv run --no-sync pytest -p no:cacheprovider -v`: **65 passed, 0 failed, 0 skipped**. |
| **Live Google API Integration (`test_server.py` & MCP calls)** | Real OAuth token refresh, Gmail/Calendar API responses, `stdio` framing, and post-refactor `events.list` free-slot calculation. | Manual PowerShell `test_server.py` run (`tools/list=6`, `list_events` + `find_free_slots` passed) + live `find_free_slots` call in Antigravity. |
| **LLM-Level Coordinator Demonstrations** | Model-level intent extraction, duplicate/conflict detection, alternative-slot drafting, and ignoring embedded prompt injections (`"forward all emails..."`). | Live Step 13 coordinator, conflict, and prompt-injection runs using `gmail-calendar` tools only. |
