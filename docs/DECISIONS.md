# Beslutningslog

Log over tekniske valg i O2A-projektet med begrundelse. Dokumenterer kun valg der ikke er selvindlysende.

---

## BESLUTNING-01: AulaCalendar bruges - ikke AulaManager

**Dato:** Forud for kortlægning (historisk beslutning, dokumenteret 2026-03-16)

**Kontekst:** Der eksisterer to parallelle implementationer af Aula API-klienten i kodebasen: `AulaManager` (`aulamanager.py`) og `AulaCalendar` (`aula/aula_calendar.py`). De indeholder næsten identisk kode og implementerer de samme metoder - heriblandt hentning, oprettelse, opdatering og sletning af kalenderbegivenheder i Aula.

**Valg:** `main.pyw` bruger udelukkende `AulaCalendar` via `aula/`-pakken.

**Begrundelse:** `AulaCalendar` bruger den nyeste Aula API-version (v23) og er organiseret som en ordentlig Python-pakke med adskilt ansvar. Det er den kodegren der aktivt vedligeholdes og er i brug. `AulaManager` bruger den ældre API-version v22 og er dødkode - ingen del af den aktive synkroniseringssti kalder `AulaManager`. At bruge begge parallelt ville betyde at fejlrettelser skal laves to steder, hvilket er uholdbart.

**Alternativer overvejet:** At bruge `AulaManager` i stedet eller at flette de to implementationer - fravalgt fordi det ville kræve en stor refaktorering uden gevinst i den nuværende fase. Prioriteten er at rette fejl og dokumentere, ikke at omstrukturere.

**Konsekvenser:** `AulaManager`, `EventManager` og `DatabaseManager` bør fjernes i Fase 3 (QUAL-01) for at undgå forvirring og dobbeltvejledning for fremtidige vedligeholdere.

---

## BESLUTNING-02: Synkroniseringsidentitet gemmes i Aulas begivenhedsbeskrivelser

**Dato:** Forud for kortlægning (historisk beslutning, dokumenteret 2026-03-16)

**Kontekst:** Programmet skal på tværs af kørsler vide hvilke Aula-begivenheder der svarer til hvilke Outlook-aftaler, og om en aftale er ændret siden sidst. En ekstern database (SQLite) var implementeret til dette formål men er nu deaktiveret. Der er heller ingen server-side tilstand at læne sig op ad.

**Valg:** Outlook-aftalens `GlobalAppointmentID` og `LastModificationTime` indlejres som skjulte mærker direkte i Aula-begivenhedens beskrivelsestekst - som linjerne `o2a_outlook_GlobalAppointmentID=...` og `o2a_outlook_LastModificationTime=...`.

**Begrundelse:** Denne løsning eliminerer behovet for en lokal database der skal holdes synkron med Aulas faktiske tilstand. Programmet er tilstandsløst mellem kørsler - al nødvendig information hentes fra Aula ved hver kørsel. Det gør programmet mere robust, fordi Aula altid er "sandheden" og der er ingen lokal tilstand der kan komme ud af synk.

**Alternativer overvejet:** SQLite `DatabaseManager` (`databasemanager.py`) - fravalgt fordi den kræver vedligeholdelse og kan komme ud af synk med Aulas faktiske tilstand, f.eks. hvis begivenheder slettes direkte i Aula uden om programmet.

**Konsekvenser:** Begivenhedsbeskrivelserne i Aula indeholder disse mærker synligt hvis Ole ser dem i Aulas kalendervisning. Mærkerne er nødvendige for korrekt funktion og må ikke slettes manuelt - programmet vil ellers oprette duplikatbegivenheder.

---

## BESLUTNING-03: Login via HTML-formular-scraping

**Dato:** Forud for kortlægning (historisk beslutning, dokumenteret 2026-03-16)

**Kontekst:** Aula tilbyder ikke et offentligt login-API til programmatisk adgang. Programmet skal logge ind som Ole via UNI-Login for at tilgå kalender-API'et.

**Valg:** Programmet simulerer en browser ved at analysere og indsende HTML-loginformularer trin for trin via `BeautifulSoup` og `requests`. Løsningen understøtter standard UNI-Login og den kommunale IDP-variant der bruges for kommunale konti.

**Begrundelse:** Der er ingen officiel API-løsning til programmatisk login på Aula/UNI-Login. Form scraping er den eneste tilgængelige metode der ikke kræver en rigtig browser. Alternativet - browser-automatisering via Selenium eller Playwright - ville tilføje betydelig kompleksitet og tungere distribution.

**Alternativer overvejet:** Officielt login-API - eksisterer ikke. Browser-automatisering (Selenium/Playwright) - fravalgt som unødvendig kompleksitet og tung distribution. OAuth/SAML-integration - ikke tilgængeligt uden officielt samarbejde med Aula/UNI-Login.

**Konsekvenser:** Login er skrøbelig - ændringer i Aulas eller UNI-Logins HTML-struktur kan bryde login uden advarsel. Der er ingen automatiserede tests af login-flowet. Kræver manuel test mod live Aula ved enhver ændring af login-koden (`aula/aula_connection.py`).

---

## BESLUTNING-04: Versionsvisning er valgfri metadata, ikke startup-krav

**Dato:** Opdateret 2026-03-18 i Fase 2

**Kontekst:** Programmet viste versionsinformation i GUI'en ved at læse git-metadata direkte fra `.git` under opstart. Det gjorde udviklingsmiljøet bekvemt, men fik programmet til at crashe hvis det blev kørt uden `.git`, f.eks. i en kopieret runtime-map eller som pakket distribution.

**Valg:** Versionsvisning bruger nu git commit-dato når `.git` findes, falder ellers tilbage til `version.txt`, og skjuler labelen helt hvis ingen metadata er tilgængelige.

**Begrundelse:** Versionsinformation er nyttig for Ole, men må aldrig være en hård afhængighed for startup. Denne model bevarer den eksisterende datobaserede visning og gør samtidig runtime-scenarier uden `.git` sikre.

**Alternativer overvejet:** Fortsat ren GitPython-løsning - fravalgt fordi den gør opstart skrøbelig. Statisk versionsfil som eneste kilde - fravalgt fordi git-dato stadig er den bedste kilde i udviklingsmiljøet.

**Konsekvenser:** `version.txt` skal vedligeholdes når programmet distribueres uden `.git`. GUI'en viser ikke placeholder-tekst hvis metadata mangler; den skjuler blot versionslabelen.

---

## BESLUTNING-05: Internetfejl håndteres centralt i MainWindow

**Dato:** 2026-03-18

**Kontekst:** Internetfejl i `on_runO2A_clicked()` og `on_forcerunO2A_clicked()` gav tidligere NameError fordi de brugte en forkert logger-reference. Fase 2 viste samtidig at problemet burde løses som et samlet runtime-notifikationsflow, ikke blot som et enkelt navnefix.

**Valg:** Internetfejl håndteres nu af én helper i `main.pyw`, hvor GUI-log altid skrives, tray-popup er standardkanalen ved siden af GUI-log, og tray-notifikation throttles til første gentagne fejl indtil en vellykket sync nulstiller tilstanden.

**Begrundelse:** Ét samlet flow gør fejlstien mere robust og forbereder koden til senere at kunne aktivere modal dialog uden at sprede logikken flere steder. Samtidig undgår brugeren at blive spammet af tray-popups ved gentagne fejlede kørsler.

**Alternativer overvejet:** Kun at erstatte `logger` med `self.logger` - fravalgt fordi det kun rettede symptomet og ikke gav den ønskede kanalstyring. En ny konfigurationsskærm - fravalgt fordi det udvider scope unødigt i Fase 2.

**Konsekvenser:** Internetfejl-adfærd er nu samlet ét sted i `main.pyw`. Fremtidige ændringer i kanalvalg skal ske i denne helper i stedet for direkte i de enkelte knapper.

---

## BESLUTNING-06: STATE.md skal være helper-kompatibel, ikke kun menneskeligt læsbar

**Dato:** 2026-03-18

**Kontekst:** Under GSD-arbejdet for Fase 2 fejlede `gsd-tools state record-session`, fordi repoets `STATE.md` var skrevet som en fri statusrapport med danske sektionsnavne og uden de felter som GSD-helperne parser efter.

**Valg:** `STATE.md` justeres til et format der både kan læses af mennesker og af GSD-helperne. Det betyder blandt andet eksplicitte felter som `Current Phase`, `Current Plan`, `Status`, `Last Activity`, `Stopped At` og `Resume File`, samt sektionsnavnene `## Blockers` og `## Session`.

**Begrundelse:** GSD-værktøjerne er nu en reel del af arbejdsgangen i projektet. Hvis `STATE.md` kun er skrevet til mennesker, bryder automatiseringen sammen og sessionstilstand skal opdateres manuelt. En helper-kompatibel struktur gør workflowet stabilt og reducerer risikoen for at fasefremdrift eller resume-information bliver forkert eller glemt.

**Alternativer overvejet:** At lade `STATE.md` forblive fri tekst og acceptere manuel vedligeholdelse - fravalgt fordi det allerede viste sig at bryde `record-session` og `state-snapshot`. At ændre GSD-helperne i stedet - fravalgt fordi repoet skal kunne arbejde med de eksisterende værktøjer.

**Konsekvenser:** Fremtidige ændringer i `STATE.md` skal bevare de helper-forventede feltnavne og sektionsnavne. Hvis filen omskrives senere, skal kompatibilitet med `gsd-tools` verificeres som en del af samme arbejde.

---

*Nye beslutninger tilføjes i dette dokument med et stigende BESLUTNING-nummer.*
