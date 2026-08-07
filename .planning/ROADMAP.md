# Roadmap: O2A — Outlook to Aula

## Oversigt

Projektet er en eksisterende, fungerende Windows-desktopapplikation. Dette roadmap dækker den første forbedringscyklus: dokumentation til Ole, rettelse af kendte kritiske fejl, oprydning i kodebasen og genaktivering af deltager-caching for bedre ydeevne. Applikationens kerneværdi — at Outlook-aftaler mærket "AULA" altid afspejler den korrekte tilstand i Aula — bevares og styrkes igennem alle faser.

## Faser

**Faseoversigt:**
- [ ] **Fase 1: Dokumentation** - Ole kan læse og forstå projektet via en dansk docs/-mappe
- [x] **Fase 2: Fejlrettelser** - Alle kendte kritiske fejl er rettet, applikationen kører stabilt
- [ ] **Fase 3: Kodekvalitet** - Dødkode er fjernet, fejlhåndtering er eksplicit og hjælpefunktioner er samlet
- [ ] **Fase 4: Ydeevne** - Deltager-caching er genaktiveret, sync-tid reduceres markant

## Fase-detaljer

### Fase 1: Dokumentation
**Mål**: Ole kan selvstændigt forstå projektets arkitektur, arbejdshistorik, tekniske beslutninger og kendte problemer via en struktureret dansk docs/-mappe
**Afhænger af**: Ingenting (første fase)
**Krav**: DOCS-01, DOCS-02, DOCS-03, DOCS-04
**Succeskriterier** (hvad der SKAL være sandt):
  1. Ole kan åbne docs/PROJECT_OVERVIEW.md og læse en samlet dansk forklaring af hvad O2A er, hvordan det virker og hvilke begrænsninger det har
  2. Ole kan følge hvad der er lavet og hvorfor i docs/WORK_LOG.md med daterede indgange for analyser og ændringer
  3. Ole kan se begrundelsen bag konkrete tekniske valg (f.eks. hvorfor AulaCalendar og ikke AulaManager) i docs/DECISIONS.md
  4. Ole kan se en opdateret liste over kendte fejl og teknisk gæld i docs/ISSUES.md og vurdere hvad der bør prioriteres
**Planer**: 3 planer

Planer:
- [x] 01-01-PLAN.md — Opret docs/-mappe og skriv PROJECT_OVERVIEW.md (DOCS-01)
- [x] 01-02-PLAN.md — Skriv WORK_LOG.md og DECISIONS.md (DOCS-02, DOCS-03)
- [x] 01-03-PLAN.md — Skriv ISSUES.md med kendte fejl og teknisk gæld (DOCS-04)

### Fase 2: Fejlrettelser
**Mål**: Alle kendte kritiske fejl er rettet så applikationen starter korrekt, kører stabilt på Python 3.12+ og synkroniserer med korrekte tidspunkter i 2026 og frem
**Afhænger af**: Fase 1 (dokumentationen giver kontekst til fejlrettelserne)
**Krav**: BUG-01, BUG-02, BUG-03, BUG-04, BUG-05
**Succeskriterier** (hvad der SKAL være sandt):
  1. En begivenhed oprettet i Outlook til juli 2026 vises med korrekt klokkeslæt i Aula (ikke en time forskudt)
  2. Applikationen starter og kører uden fejl på Python 3.12 og Python 3.13
  3. Når internetforbindelsen mangler ved synkroniseringsstart, vises en fejlbesked i GUI-logpanelet i stedet for et crash
  4. Sletning af en Aula-begivenhed gennemføres uden NameError, også når sletningen mislykkes første gang
  5. Applikationen starter korrekt når den køres som kompileret .exe uden .git-mappe til stede
**Planer**: TBD

Planer:
- [x] 02-01: Ret BUG-01 (hardkodet DST-tabel) og BUG-02 (distutils-import)
- [x] 02-02: Ret BUG-03 (logger-referencefejl), BUG-04 (syntaksfejl i deleteEvent) og BUG-05 (GitPython-crash)

### Fase 3: Kodekvalitet
**Mål**: Kodebasen er ryddet for dødkode, fejlhåndtering er eksplicit og loggede, og duplikerede hjælpefunktioner er samlet ét sted
**Afhænger af**: Fase 2 (bugs rettet før dødkode fjernes, for ikke at miste fejlsporingskontekst)
**Krav**: QUAL-01, QUAL-02, QUAL-03
**Succeskriterier** (hvad der SKAL være sandt):
  1. Filerne aulamanager.py, eventmanager.py og databasemanager.py er fjernet fra kodebasen (eller reduceret til tomme stubs), og applikationen starter og synkroniserer korrekt uden dem
  2. En mislykkedes login eller API-kald producerer en konkret, loggede fejlbesked i GUI-logpanelet i stedet for at blive slugt tavst af et bare except-blok
  3. url_fixer, teams_url_fixer og calulate_day_of_the_week_mask importeres udelukkende fra aula/utils.py — ingen duplikater i aula_calendar.py eller andre filer
**Planer**: TBD

Planer:
- [ ] 03-01: Fjern AulaManager, EventManager og DatabaseManager (QUAL-01)
- [ ] 03-02: Erstat bare except-blokke med eksplicit fejlhåndtering og logging (QUAL-02)
- [ ] 03-03: Saml hjælpefunktioner i aula/utils.py og opdater imports (QUAL-03)

### Fase 4: Ydeevne
**Mål**: Deltagernavne caches lokalt per sync-session så hvert navn kun slås op én gang, og synkroniseringstiden reduceres markant ved mange begivenheder med deltagere
**Afhænger af**: Fase 3 (dødkode er fjernet; en ny eller forenklet cache-løsning kan implementeres rent)
**Krav**: PERF-01
**Succeskriterier** (hvad der SKAL være sandt):
  1. Ved en sync-kørsel med 10 begivenheder der deler deltagere slås hvert deltager-navn op højst én gang i Aula-søge-API'et i stedet for én gang per begivenhed
  2. Gensynkronisering af en uændret kalender med kendte deltagere er mærkbart hurtigere end ved første kørsel samme session
**Planer**: TBD

Planer:
- [ ] 04-01: Genaktiver deltager-caching via en in-memory dict per sync-session (PERF-01)

## Fremgang

**Udførelsesrækkefølge:** 1 → 2 → 3 → 4

| Fase | Planer fuldført | Status | Afsluttet |
|------|-----------------|--------|-----------|
| 1. Dokumentation | 3/3 | Complete   | 2026-03-16 |
| 2. Fejlrettelser | 2/2 | Complete | 2026-03-18 |
| 3. Kodekvalitet | 0/3 | Ikke startet | - |
| 4. Ydeevne | 0/1 | Ikke startet | - |

## Backlog

### Fase 999.1: UX-forbedringer til GUI (fra designgennemgang) (BACKLOG)

**Mål:** Gøre programmet mere brugervenligt uden at fjerne eksisterende funktionalitet
**Krav:** TBD
**Planer:** 0 planer — se `.planning/phases/999.1-ux-forbedringer-til-gui-baseret-paa-designgennemgang/NOTES.md` for de 6 konkrete forslag

Planer:
- [ ] TBD (forfrem med /gsd-review-backlog når prioriteret)
