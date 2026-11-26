# Beginner's Guide — Running L07 `gmail-calendar` on Windows

This guide explains how to set up, test, and operate the `gmail-calendar` MCP server in `C:\Users\User\L07` using **Windows PowerShell** and **Antigravity**.

## 1. Prerequisites

- **Windows PowerShell** (PowerShell 7 or Windows PowerShell)
- **Python 3.12+** and **`uv`**
- **Git** (for version control)
- **External Google OAuth directory** outside `C:\Users\User\L07` containing your pre-authorized `credentials.json` and `token.json` (for example, `C:\path\to\.meetbridge`)

> **Important:** Never copy `credentials.json`, `token.json`, or `.env` files into `C:\Users\User\L07`.

## 2. Install Dependencies in PowerShell

Open PowerShell in `C:\Users\User\L07` and sync the `uv` virtual environment:

```powershell
cd C:\Users\User\L07
uv sync
```

## 3. Run Automated Mocked Tests (`pytest`)

These tests use mocked Google APIs and run safely offline without touching your Gmail or Calendar:

```powershell
uv run --no-sync pytest -p no:cacheprovider -v
```

Expected outcome: `65 passed`.

## 4. Run the Live Google API Integration Test

Point `GOOGLE_PRIVATE_DIR` to your external OAuth directory and run `test_server.py`:

```powershell
$env:GOOGLE_PRIVATE_DIR = "C:\path\to\.meetbridge"
uv run --no-sync python -B test_server.py
```

Expected output confirms `MCP initialized: gmail-calendar`, `tools/list count: 6`, `list_events SUCCEEDED`, and `find_free_slots SUCCEEDED`.

## 5. Connect to Antigravity

Ensure `.agents\mcp_config.json` (ignored by Git via `mcp_config*.json` in `.gitignore`) points to `uv.exe` and your external `GOOGLE_PRIVATE_DIR`:

```json
{
  "mcpServers": {
    "gmail-calendar": {
      "command": "C:\\Users\\User\\.local\\bin\\uv.exe",
      "args": ["run", "--directory", "C:\\Users\\User\\L07", "server.py"],
      "env": {
        "GOOGLE_PRIVATE_DIR": "C:\\path\\to\\.meetbridge"
      }
    }
  }
}
```

### Safe Example Prompts in Antigravity
- *"What do I have in my calendar tomorrow in Asia/Jerusalem time?"*
- *"Find a free 45-minute slot tomorrow between 09:00 and 17:00."*
- *"Read my latest meeting request, check for conflicts or duplicates, and prepare a reply draft without sending."*

## 6. Common Troubleshooting

- **HTTP 403 `insufficientPermissions` in `find_free_slots`:** Ensure you are running the updated `server.py` + `calendar_helpers.py` (which uses `events.list` instead of `freeBusy`) and restart Antigravity's MCP server process if an older process was still running.
- **`GOOGLE_PRIVATE_DIR` or missing file errors:** Confirm `$env:GOOGLE_PRIVATE_DIR` is set to the external folder containing both `credentials.json` and `token.json`.
- **Expired/unrefreshable token:** The MCP server intentionally never opens a browser. Re-authorize your external `token.json` outside the MCP server if `refresh_token` is missing or revoked.
- **`PytestCacheWarning` in restricted sandboxes:** Pass `-p no:cacheprovider` to `pytest`.
