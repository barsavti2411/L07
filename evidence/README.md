# L07 Evidence Screenshots

This directory holds authentic screenshots demonstrating the current L07 `gmail-calendar` MCP assignment. Do **not** place placeholder images, credentials, tokens, API keys, personal email addresses, or private identifiers inside screenshots.

## Mandatory Course Screenshots (3 Required — All Present)

1. **`01_mcp_connected.png`** — **MCP Server Connected & Six Tools Visible**
   - Shows `/mcp` in Antigravity with `gmail-calendar` connected (`✓`) and displaying its tools (`search_emails, read_email, create_draft, list_events, find_free_slots, +1 more` = 6 tools).
2. **`02_agent_request.png`** — **Natural-Language Request Submitted to the Agent**
   - Shows the natural-language prompt submitted to Antigravity requesting upcoming 7-day events and available 45-minute slots on December 1, 2026 (`Asia/Jerusalem`, read-only).
3. **`03_execution_result.png`** — **Successful Execution Result**
   - Shows the agent calling `gmail-calendar/list_events` and `gmail-calendar/find_free_slots` and returning upcoming events and open slots in `Asia/Jerusalem` time.

## Existing Supplementary Screenshots (3 Present)

4. **`04_gmail_draft.png`** — Gmail web UI (`in:draft`) showing three unsent drafts created during testing (`L07 test`, `Re: Meeting request`, `Re: Meeting request - Conflict test`).
5. **`05_calendar_event.png`** — Google Calendar week view (`GMT+2`) showing the scheduled `Study group` event (`9 – 10am`).
6. **`05_calendar_event_detail.png`** — Google Calendar day view (`November 26, 2026`, `GMT+2`) showing the `Study group` event (`9 – 10am`) in detail.

## Optional Supplementary Screenshots (Not Captured)

- `06_free_slots.png` *(Note: `find_free_slots` output is currently shown inside `03_execution_result.png`; no separate file captured)*
- `07_meeting_coordinator.png` *(Optional — not captured)*
- `08_conflict_resolution.png` *(Optional — not captured)*
- `09_prompt_injection.png` *(Optional — not captured)*
- `10_65_tests_passed.png` *(Optional — not captured)*
- `11_live_integration.png` *(Optional — not captured)*
- `12_git_security.png` *(Optional — not captured)*

## Screenshot Checklist

- [x] `01_mcp_connected.png` *(Mandatory)*
- [x] `02_agent_request.png` *(Mandatory)*
- [x] `03_execution_result.png` *(Mandatory)*
- [x] `04_gmail_draft.png` *(Supplementary — captured)*
- [x] `05_calendar_event.png` *(Supplementary — captured)*
- [x] `05_calendar_event_detail.png` *(Supplementary — captured)*
- [ ] `06_free_slots.png` *(Optional — not captured separately)*
- [ ] `07_meeting_coordinator.png` *(Optional — not captured)*
- [ ] `08_conflict_resolution.png` *(Optional — not captured)*
- [ ] `09_prompt_injection.png` *(Optional — not captured)*
- [ ] `10_65_tests_passed.png` *(Optional — not captured)*
- [ ] `11_live_integration.png` *(Optional — not captured)*
- [ ] `12_git_security.png` *(Optional — not captured)*
