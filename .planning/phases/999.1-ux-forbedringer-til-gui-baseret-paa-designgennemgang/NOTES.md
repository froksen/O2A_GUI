# Backlog 999.1: UX-forbedringer til GUI (fra designgennemgang)

**Fanget:** 2026-08-07, i en samtale hvor hele `ui/`-mappen blev gennemgået
(`theme.py`, `shell.py`, `status_view.py`, `widgets.py`, `settings_view.py`,
`personer_view.py`, `konto_view.py`, `notifikationer_view.py`,
`dialogs/wizard.py`).

**Formål:** Gøre programmet mere brugervenligt uden at fjerne eksisterende
funktionalitet. Ingen af punkterne er besluttet eller prioriteret af Ole
endnu — rækkefølgen nedenfor er et forslag, ikke en beslutning.

---

## 1. Personer-siden mangler reelt UI (størst gevinst)

**Fil:** `ui/personer_view.py`

I dag gør "Ignorer personer" og "Personers alias" kun ét: åbner en rå CSV-fil
i Excel via `os.system(f'start excel.exe "{filename}"')`
(se `mainwindow.py::_open_excel`, kaldt fra
`on_actionIgnore_people_list_triggered` / `on_actionOutlook_Aulanavne_liste_triggered`).
Brugeren skal forlade appen, redigere en fil uden formathjælp, gemme og håbe
formatet er korrekt.

**Forslag:** Byg en simpel in-app tabel-editor direkte i `PersonerView`
(tilføj/fjern/redigér rækker for hhv. ignorerliste og alias-mapping).
Behold "Åbn i Excel" som sekundær/avanceret mulighed — fjern intet.

**Relevante filer at kende til:** `peoplecsvmanager.py` (læser/skriver CSV'erne),
`personer_skabelon.csv`, `personer_ignorer_skabelon.csv` (skabeloner der
kopieres ved første kørsel).

---

## 2. Ingen forklaring FØR valg af synkroniseringsadfærd

**Fil:** `ui/settings_view.py`

Radioknapperne for `SYNC_BEHAVIOR_OPTIONS` (defineret i `setupmanager.py`)
har allerede en advarselsdialog der fyrer EFTER man skifter til en adfærd
med mange begivenheder (`mainwindow.py::on_sync_behavior_changed`,
`_SYNC_BEHAVIORS_WITH_MANY_EVENTS`), men ingen inline-hjælp der forklarer
konsekvensen af hvert valg FØR man klikker.

**Forslag:** Tilføj et infoikon eller en kort undertekst under hver
radio-label, der forklarer hvad valget betyder (samme information som
allerede findes i advarselsteksten, bare vist proaktivt).

---

## 3. Status-siden: sammendrags-tiles er ikke klikbare

**Fil:** `ui/status_view.py`

"Oprettet"/"Opdateret"/"Fjernet"/"Fejl"-tiles (`_tile_labels`) er statiske
tal. Begivenhedslisten nedenunder (`_render_events`, læser fra
`ui/event_store.py::EventStore`) tagger allerede hver post med
action-type (`oprettet`/`opdateret`/`fjernet`) og fejl-status.

**Forslag:** Gør tiles klikbare, så de filtrerer event-feedet efter type.
Datagrundlaget findes allerede — det er en visningsændring, ikke en
datamodel-ændring.

---

## 4. To næsten-ens indstillinger uden forklaring

**Fil:** `ui/settings_view.py`

"Åben programmet i baggrunden" (`_start_minimized_var`, styrer om vinduet
skjules ved håndstart) og "Start Outlook2Aula automatisk"
(`_run_at_startup_var`, opretter en Windows-opstartsgenvej via
`winshell.CreateShortcut` i `mainwindow.py::_create_shortcut`) lyder næsten
identiske men gør forskellige ting.

**Forslag:** Tilføj en kort undertekst under hver checkbox der forklarer
forskellen.

---

## 5. Konto-siden viser kun hvem, ikke om login virker

**Fil:** `ui/konto_view.py`

Siden viser i dag kun brugernavn + IDP-metode + en "Konfigurer login"-knap.
Der er ingen visning af seneste login-status eller -tidspunkt, selvom det
er her en bruger naturligt ville lede efter årsagen til en synk-fejl.

**Forslag:** Vis seneste login-status/-tidspunkt på siden. Kræver formentlig
at login-resultatet fra `aula/aula_connection.py::AulaConnection.login()`
gemmes et sted (fx via `setupmanager.py`) så det kan læses igen efter en
sync er afsluttet.

---

## 6. Bonus-fund: tredje duplikeret version-detektionslogik

**Ikke en UX-ting**, men fundet under designgennemgangen og direkte relateret
til dedupliceringsarbejdet fra en tidligere session (se commit
"refactor: ryd op i kodebasen" på branchen `optimize/code-performance`).

`ui/widgets.py::VersionLabel._get_version()` er en **tredje** kopi af
samme logik (git-commit-dato, ellers `version.txt`-fallback), som allerede
blev samlet ét sted mellem `mainwindow.py` og `ui/opdater_view.py`
(`OpdaterView._get_program_version()`) tidligere. Bør konsolideres
til én fælles helper (fx `aula/utils.py` eller en ny lille modul),
så der kun er ét sted at rette version-visningslogik.

---

## Status

Ingen af punkterne er startet. Brug `/gsd-discuss-phase 999.1` for at
udforske videre, eller `/gsd-review-backlog` for at forfremme til en
aktiv milestone når Ole har prioriteret.
