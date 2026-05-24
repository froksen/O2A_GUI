# Architecture

**Analysis Date:** 2026-03-16

## Pattern Overview

**Overall:** Manager-based service architecture with a PySide6 GUI frontend and background worker threading

**Key Characteristics:**
- Single Windows desktop application with system tray support
- Background sync jobs dispatched via `QThreadPool` + `QRunnable` workers to keep the GUI responsive
- All calendar synchronization logic lives in `main.pyw` orchestrated through specialized manager classes
- Qt signals/slots used for cross-thread communication between workers and the GUI

## Layers

**Presentation Layer:**
- Purpose: Qt-based GUI, dialog management, system tray, user interaction
- Location: `main.pyw`, `mainwindow.py`, `mainwindow.ui`, `unilogindialog.py`, `unilogindialog.ui`
- Contains: `MainWindow`, `UniloginDialog`, `Worker`, `WorkerSignals`, `QtHandler`, `Signaller`
- Depends on: All manager classes and the `aula` package
- Used by: End user; entry point `main.pyw`

**Aula Integration Layer:**
- Purpose: Authenticates to Aula, retrieves and mutates calendar events via the Aula REST API
- Location: `aula/` package (`aula_connection.py`, `aula_calendar.py`, `aula_event.py`, `aula_common.py`, `utils.py`)
- Contains: `AulaConnection` (HTTP session + login), `AulaCalendar` (CRUD operations on events), `AulaEvent` (domain model)
- Depends on: `requests`, `BeautifulSoup`, `PeopleCsvManager`
- Used by: `main.pyw`, `eventmanager.py`

**Outlook Integration Layer:**
- Purpose: Reads events from the local Outlook calendar via COM interop
- Location: `outlookmanager.py`
- Contains: `OutlookManager` — reads calendar items, sends notification emails through Outlook
- Depends on: `win32com.client`, `pywin32`
- Used by: `main.pyw`, `eventmanager.py`

**Comparison Layer:**
- Purpose: Diffs two event dictionaries (keyed by GlobalAppointmentID) to determine creates, updates, and deletes
- Location: `calendar_comparer.py`
- Contains: `CalendarComparer`
- Depends on: Nothing external
- Used by: `main.pyw` (`update_calendar`)

**Configuration / Setup Layer:**
- Purpose: Persists user credentials and application settings; manages Outlook categories
- Location: `setupmanager.py`
- Contains: `SetupManager` — reads/writes `configuration.ini`, stores password in OS keyring
- Depends on: `keyring`, `configparser`, `win32com.client`
- Used by: `main.pyw`, `eventmanager.py`

**People/Alias Layer:**
- Purpose: Maps Outlook attendee display names to Aula names, and maintains an ignore list
- Location: `peoplecsvmanager.py`
- Contains: `PeopleCsvManager` — reads `personer.csv` and `personer_ignorer.csv`
- Depends on: `csv`
- Used by: `aula/aula_calendar.py`, `eventmanager.py`

**Legacy / Unused Layer:**
- Purpose: Earlier database-backed approach to event tracking; now largely superseded by embedding IDs in Aula event descriptions
- Location: `databasemanager.py`, `databaseevent.py`, `eventmanager.py`, `aulamanager.py`
- Contains: `DatabaseManager` (SQLite), `DatabaseEvent`, `EventManager`, `AulaManager`
- Depends on: `sqlite3`
- Used by: Not called from the active sync path in `main.pyw`

## Data Flow

**Primary Sync Flow (triggered by timer or manual button):**

1. `MainWindow.on_runO2A_clicked` (or timer fires) creates a `Worker(self.update_calendar, force_update=False)` and submits it to `QThreadPool`
2. `Worker.run` calls `MainWindow.update_calendar` on a background thread
3. `SetupManager` reads credentials from `configuration.ini` / OS keyring
4. `AulaConnection.login` authenticates to `https://login.aula.dk` via multi-step HTML form scraping with `requests` + `BeautifulSoup`; stores authenticated `requests.Session`
5. `OutlookManager.get_aulaevents_from_outlook` reads Outlook calendar items via COM, filtering for items categorised as "AULA" or "AULA Institutionskalender"; returns `dict[GlobalAppointmentID → event dict]`
6. `AulaCalendar.getEvents` pages through months, calling Aula REST API (`calendar.getEventsForInstitutions` and `calendar.getEventsByProfileIdsAndResourceIds`), parses embedded `o2a_outlook_GlobalAppointmentID` and `o2a_outlook_LastModificationTime` markers from each event description; returns `dict[GlobalAppointmentID → event dict]`
7. `CalendarComparer` performs set operations on the two dictionaries' keys to produce `unique_to_aula` (to delete), `unique_to_outlook` (to create), and `identical` (to check for updates)
8. `MainWindow.__delete_aula_events` calls `AulaCalendar.deleteEvent` for each removal
9. `MainWindow.__create_aula_events` converts Outlook items to `AulaEvent` via `AulaCalendar.convert_outlook_appointmentitem_to_aula_event`, resolves attendee Aula IDs via `AulaCalendar.get_atendees_ids`, then calls `AulaCalendar.createSimpleEvent`
10. `MainWindow.__update_aula_events` checks `LastModificationTime` (unless `force_update=True`) and calls `AulaCalendar.updateEvent` if changed
11. If any events had creation/update errors, `OutlookManager.send_a_aula_creation_or_update_error_mail` sends an HTML email to the user via Outlook COM

**State Management:**
- No persistent in-memory state between sync runs; each run re-authenticates and re-fetches
- Sync ID embedded directly in the Aula event description as `o2a_outlook_GlobalAppointmentID=<id>` and `o2a_outlook_LastModificationTime=<ts>` — this is the only cross-run state
- `configuration.ini` stores username and GUI preferences; OS keyring stores the password

## Key Abstractions

**AulaEvent:**
- Purpose: Domain model for a single calendar event in Aula-compatible format
- Examples: `aula/aula_event.py`
- Pattern: Plain data class with computed `@property` accessors for `start_date_time`, `end_date_time`, and `description` (the description property embeds the sync markers)

**AulaConnection:**
- Purpose: Wraps an authenticated `requests.Session` plus profile data retrieved after login
- Examples: `aula/aula_connection.py`
- Pattern: Stateful object; must call `login(username, password)` before other methods. Supports two login paths: STIL (standard UNI-login) and a municipal IDP path

**AulaCalendar:**
- Purpose: All CRUD operations against the Aula calendar API; constructed from an `AulaConnection`
- Examples: `aula/aula_calendar.py`
- Pattern: Thin service wrapper; receives an `AulaConnection` in constructor, delegates HTTP calls to the stored session

**Worker / WorkerSignals:**
- Purpose: Qt thread pool worker that wraps any callable, emits `finished`, `result`, and `error` signals
- Examples: `main.pyw` lines 47–116
- Pattern: Generic reusable pattern — `Worker(fn, *args, **kwargs)` injects a `progress_callback` kwarg into the call

## Entry Points

**Application Entry:**
- Location: `main.pyw` (the `if __name__ == "__main__":` block, lines 613–689)
- Triggers: Launched directly by Python or via `updateandrun.bat` / Windows startup shortcut
- Responsibilities: Creates `QApplication`, `MainWindow`, system tray icon, configures the `logging` hierarchy (file handler → `o2a.log`, stream handler → stdout, Qt handler → GUI log panel)

**Sync Entry:**
- Location: `MainWindow.update_calendar` in `main.pyw` (line 348)
- Triggers: Manual button click (`runO2A`, `forcerunO2A`) or the `QTimer`-driven frequency timer
- Responsibilities: Full Outlook→Aula diff-and-sync pipeline

## Error Handling

**Strategy:** Log-and-continue with optional email notification to the user

**Patterns:**
- `Worker.run` wraps the sync callable in a broad `try/except`; emits `signals.error` on failure
- Per-event errors tracked in `AulaEvent.creation_or_update_errors` (`AulaEventCreationErrors` instance) and collected into a list; at the end of a sync run the list is passed to `OutlookManager.send_a_aula_creation_or_update_error_mail`
- Login errors surfaced via `LoginStatus.error_messages` list and emailed via `OutlookManager.send_a_mail`
- Many exception handlers use bare `except: pass` — errors silently swallowed in the login scraping loop

## Cross-Cutting Concerns

**Logging:** Python `logging` module with logger name `'O2A'`; three handlers configured in `main.pyw`: `FileHandler('o2a.log')`, `StreamHandler` (stdout), `QtHandler` (routes to the GUI log panel using Qt signals). Log levels: DEBUG to file/stdout, INFO to GUI.

**Validation:** Minimal; attendee name resolution via `PeopleCsvManager` provides name-mapping and ignore-list functionality. No schema validation on API responses.

**Authentication:** Multi-step HTML form scraping using `requests.Session` + `BeautifulSoup`. Credentials stored in OS keyring (`keyring` library) and username in `configuration.ini`. Two login paths detected by username pattern match.

---

*Architecture analysis: 2026-03-16*
