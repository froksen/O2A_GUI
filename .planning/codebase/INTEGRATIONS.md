# External Integrations

**Analysis Date:** 2026-03-16

## APIs & External Services

**Aula (Danish school portal):**
- Purpose: Create, update, delete, and read calendar events on the Aula platform
- Base URL: `https://www.aula.dk/api/v23/`
- Client: Custom HTTP client using `requests.Session` in `aula/aula_connection.py`
- Auth: Session-based (cookie + CSRF token), see Authentication section below
- API style: Single-endpoint RPC with `?method=` query parameter
- Methods used:
  - `profiles.getProfilesByLogin` - Fetch employee profile ID and institution code after login
  - `calendar.getEventsForInstitutions` - List institution calendar events
  - `calendar.getEventsByProfileIdsAndResourceIds` - List personal calendar events
  - `calendar.getEventById` - Fetch full event details
  - `calendar.createSimpleEvent` - Create a new event
  - `calendar.updateSimpleEvent` - Update an existing event
  - `calendar.deleteEvent` - Delete an event
  - `search.findRecipients` - Search for attendees by name

**UNI-Login (Danish national identity provider):**
- Purpose: Authentication gateway for Aula; handles form-based SSO login
- Login URL: `https://login.aula.dk/auth/login.php?type=unilogin`
- Client: `requests.Session` with HTML form scraping via `beautifulsoup4` (`aula/aula_connection.py`)
- Two login paths supported:
  1. Standard STIL UNI-Login: `login_with_stil()` - username/password via form fields
  2. Municipal IDP: `login_with_idp()` - routes through a municipal IDP endpoint; detected by regex pattern `^\w{8}@skolens\.net$`
- Session success detected by checking redirect to `https://www.aula.dk:443/portal/`
- CSRF token extracted from cookie `Csrfp-Token` and injected into session headers as `csrfp-token`

**Microsoft Outlook (via COM automation):**
- Purpose: Source of calendar events to sync to Aula; also used to send error notification emails
- SDK/Client: `win32com.client.Dispatch("Outlook.Application")` from `pywin32` package
- Used in: `outlookmanager.py`, `setupmanager.py`
- Operations:
  - Read personal calendar items filtered by date range and Outlook category
  - Create and send HTML emails to the current Exchange user
  - Read/create Outlook categories (`AULA`, `AULA Institutionskalender`)
  - Access Exchange user profile and primary SMTP address
- Requires: Outlook installed and running on Windows; MAPI namespace (`ns.GetNamespace("MAPI")`)

**Internet Connectivity Check:**
- Purpose: Pre-flight check before each sync run
- Target: `https://www.google.dk/` with 5-second timeout
- Location: `main.pyw` `has_internet_connection()`

## Data Storage

**Databases:**
- Type: SQLite (file-based, local)
- File: `database.db` (created at runtime in working directory)
- Client: `sqlite3` stdlib, managed by `databasemanager.py`
- Tables:
  - `tblEvents` - Maps Outlook appointment IDs to Aula event IDs (create/update tracking)
  - `tblRecipients` - Caches Aula profile IDs by name
- Note: `DatabaseManager` exists in codebase but is NOT currently called from main sync flow. The live sync instead embeds tracking metadata (`o2a_outlook_GlobalAppointmentID`, `o2a_outlook_LastModificationTime`) directly into Aula event descriptions as hidden markers.

**File Storage:**
- `personer.csv` - Outlook-to-Aula name alias mapping (semicolon-delimited, runtime, user-maintained)
- `personer_ignorer.csv` - Names to skip silently during attendee lookup
- `o2a.log` - Rotating log file written to working directory
- `configuration.ini` - Application config (Aula username, GUI preferences)
- Templates: `personer_skabelon.csv`, `personer_ignorer_skabelon.csv` copied on first run

**Caching:**
- In-memory only during a sync run (no persistent cache for Aula API responses)
- SQLite recipient cache in `tblRecipients` exists but is unused in main flow

## Authentication & Identity

**Auth Provider: UNI-Login / Aula**
- Implementation: Form-scraping loop (max 10 iterations) in `aula/aula_connection.py`
- Credentials storage: Username in `configuration.ini` (`[AULA]` section); password in OS keyring via `keyring` package (service `o2a`, account `aula_password`)
- Credential management UI: `unilogindialog.py` / `unilogindialog.ui` (PySide6 dialog) and legacy Tkinter dialog in `setupmanager.py`
- Session persisted for duration of one sync run as `requests.Session` object

## Monitoring & Observability

**Error Tracking:**
- Custom: Error conditions trigger HTML emails sent via Outlook COM to the current user
- Three email types in `outlookmanager.py`:
  - `send_a_mail()` - Login failure notification
  - `send_a_mail_program()` - Internal/program error notification (also CC'd to `olex3397@skolens.net`)
  - `send_a_aula_creation_or_update_error_mail()` - Event creation/update failure details

**Logs:**
- File handler: `o2a.log` in working directory, level DEBUG, format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- Console handler: stdout, level DEBUG
- GUI handler: Custom `QtHandler` feeding log records to `QTextEdit` widget in main window, level INFO, color-coded by level (DEBUG=black, INFO=blue, WARNING=orange, ERROR=red, CRITICAL=purple)
- Logger name: `O2A` used throughout all modules

## CI/CD & Deployment

**Hosting:**
- Local Windows desktop application; no server deployment

**Distribution:**
- Primary: Git repository cloned to user machine; `updateandrun.bat` performs `git reset --hard origin/master`, pip install, then launches `main.pyw`
- Alternative: PyInstaller-built executable via `O2A.spec` (produces `O2A` binary, UPX compressed)

**Auto-start:**
- Optional Windows startup shortcut (`.lnk`) created in user startup folder via `winshell`
- Target: `updateandrun.bat` so each startup fetches latest code

**Version Display:**
- Program version shown in GUI as latest git commit date, read via `GitPython` at startup in `main.pyw`

## Webhooks & Callbacks

**Incoming:** None - application is purely client-initiated polling

**Outgoing:** None - no webhooks sent; communication is request/response only

---

*Integration audit: 2026-03-16*
