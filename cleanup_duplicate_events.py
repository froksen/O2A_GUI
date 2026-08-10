# -*- coding: utf-8 -*-
"""
cleanup_duplicate_events.py — Rydder op i AULA-begivenheder som O2A har
oprettet som dubletter af en tidligere, fejlslagen synkronisering (se
aula_calendar.py: getEventById-hentningen kunne rate-limites af AULA uden
retry, hvilket fik allerede-oprettede begivenheder til at fremstå som
manglende og blive oprettet igen).

Virkemåde:
  1. Logger ind i AULA med de konfigurerede login-oplysninger.
  2. Henter alle AULA-begivenheder som O2A selv har oprettet (samme
     vandmærke-baserede genkendelse som den almindelige synk bruger).
  3. Grupperer dem efter deres Outlook GlobalAppointmentID — grupper med
     mere end én begivenhed er dubletter af samme Outlook-aftale.
  4. For hver dublet-gruppe beholdes den ÆLDSTE begivenhed (laveste AULA-id,
     dvs. den oprindelige), og resten slettes.

De samme funktioner bruges også af "Avanceret"-siden i selve programmet
(ui/advanceret_view.py) — dette script er blot en kommandolinje-indpakning
til at køre dem uden GUI'en.

Kører som standard i "tør" (dry-run) tilstand og sletter INTET — den viser
kun hvad den ville gøre. Kør med --execute for faktisk at slette dubletterne.

Brug:
    python cleanup_duplicate_events.py            # kun rapport, sletter intet
    python cleanup_duplicate_events.py --execute   # sletter de fundne dubletter
"""
import argparse
import collections
import datetime as dt
import logging
import sys

from dateutil.relativedelta import relativedelta, SU

from setupmanager import SetupManager
from aula import AulaCalendar, AulaConnection

logger = logging.getLogger("O2A")


def sync_window():
    """Samme datovindue som den almindelige synk bruger (mainwindow.update_calendar)."""
    today = dt.datetime.today()
    last_sunday = today + relativedelta(weekday=SU(-1))
    begin = dt.datetime(last_sunday.year, last_sunday.month, last_sunday.day, 1, 0, 0)
    end = dt.datetime(today.year + 1, 7, 1, 0, 0, 0)
    return begin, end


def fetch_own_events_raw(aula_calendar: AulaCalendar, begin: dt.datetime, end: dt.datetime,
                          progress_callback=None):
    """Henter alle egne AULA-begivenheder (type 'event', oprettet af os selv)
    som RÅ enkeltposter — i modsætning til AulaCalendar.getEvents(), som
    samler dem i en dict nøglet på Outlook-ID og dermed skjuler dubletter
    (den sidst behandlede vinder). Her skal vi netop se ALLE posterne."""
    months_diff = abs((end.year - begin.year)) * 12 + abs(end.month - begin.month)
    if months_diff <= 0:
        months_diff = 1

    raw_events = []
    for month in range(months_diff):
        lookup_begin = begin + relativedelta(months=month)
        lookup_end = begin + relativedelta(months=month + 1)
        if lookup_end >= end:
            lookup_end = end

        start_text = aula_calendar._format_lookup_datetime(lookup_begin)
        end_text = aula_calendar._format_lookup_datetime(lookup_end)

        if progress_callback:
            progress_callback(f"Henter begivenheder fra {start_text} til {end_text}…")
        else:
            logger.info(f"Henter begivenheder fra {start_text} til {end_text}…")
        raw_events += aula_calendar.getEventsByProfileIdsAndResourceIds(
            aula_calendar._profile_id, start_text, end_text)

    return raw_events


def group_by_outlook_id(aula_calendar: AulaCalendar, raw_events: list, progress_callback=None):
    """Henter fulde detaljer for hver rå begivenhed (fra den lokale cache
    hvor muligt — se aula_event_cache.py) og grupperer dem efter deres
    Outlook GlobalAppointmentID-vandmærke. Begivenheder uden vandmærke (ikke
    oprettet af O2A) sorteres fra."""
    groups = collections.defaultdict(list)
    seen_ids = set()
    total = len(raw_events)

    for i, event in enumerate(raw_events, start=1):
        event_id = event["id"]
        if event_id in seen_ids:
            continue  # samme begivenhed kan optræde i flere måneders vindue ved kant-overlap
        seen_ids.add(event_id)

        if progress_callback:
            progress_callback(i, total)
        elif i % 25 == 0 or i == total:
            logger.info(f"Læser begivenhedsdetaljer… ({i} af {total})")

        entry, _from_cache, _fetch_failed = aula_calendar.get_event_details_cached(event_id)
        if entry is None:
            continue  # kunne ikke hentes, eller ikke oprettet af O2A — rør den ikke

        groups[entry["global_id"]].append({
            "id": event_id,
            "title": entry["title"],
            "start": entry["start"],
            "created": entry.get("created"),
        })

    return groups


def find_duplicates(aula_calendar: AulaCalendar, progress_callback=None):
    """Fuld scanning: henter + grupperer, og returnerer kun grupperne med
    mere end én begivenhed (de reelle dubletter)."""
    begin, end = sync_window()
    raw_events = fetch_own_events_raw(aula_calendar, begin, end, progress_callback=progress_callback)
    groups = group_by_outlook_id(aula_calendar, raw_events, progress_callback=progress_callback)
    return {k: v for k, v in groups.items() if len(v) > 1}


def build_duplicate_report(duplicate_groups: dict):
    """Slår resultatet af find_duplicates() om til en liste af rapport-rækker,
    én pr. dublet-gruppe: hvem beholdes (ældste/laveste id), hvem slettes."""
    report = []
    for global_id, members in duplicate_groups.items():
        members_sorted = sorted(members, key=lambda m: m["id"])  # laveste id = ældst = beholdes
        report.append({
            "global_id": global_id,
            "title": members_sorted[0]["title"] or "(uden titel)",
            "start": members_sorted[0]["start"] or "?",
            "keeper": members_sorted[0],
            "losers": members_sorted[1:],
        })
    return report


def delete_duplicates(aula_calendar: AulaCalendar, to_delete: list, progress_callback=None):
    """Sletter de givne begivenheder (liste af de 'losers'-dicts fra
    build_duplicate_report). Returnerer (antal_slettet, antal_fejlet)."""
    deleted, failed = 0, 0
    total = len(to_delete)
    for i, loser in enumerate(to_delete, start=1):
        text = f"Sletter ({i} af {total}): \"{loser['title']}\""
        if progress_callback:
            progress_callback(text)
        else:
            logger.info(text)
        if aula_calendar.deleteEvent(loser["id"]):
            deleted += 1
        else:
            failed += 1
            logger.warning(f"Kunne ikke slette begivenhed {loser['id']}.")
    return deleted, failed


def login(username=None, password=None, idp_id=None):
    """Bekvemmelighedsfunktion til CLI-brug: opretter forbindelse og logger
    ind med de gemte O2A-loginoplysninger. Returnerer en klar AulaCalendar."""
    setupmgr = SetupManager()
    username = username or setupmgr.get_aula_username()
    password = password or setupmgr.get_aula_password()
    idp_id = idp_id if idp_id is not None else setupmgr.get_aula_idp_id()

    aula_connection = AulaConnection()
    login_status = aula_connection.login(username, password, idp_id=idp_id or None)
    if not login_status.status:
        return None
    return AulaCalendar(aula_connection=aula_connection)


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--execute", action="store_true",
                        help="Slet faktisk de fundne dubletter. Uden dette flag laves kun en rapport.")
    args = parser.parse_args()

    setupmgr = SetupManager()
    if not setupmgr.is_aula_configured():
        logger.error("AULA-login er ikke konfigureret endnu. Kør programmet og gennemfør opsætningen først.")
        sys.exit(1)

    logger.info("Logger ind i AULA…")
    aula_calendar = login()
    if aula_calendar is None:
        logger.error("Login mislykkedes — tjek dine loginoplysninger under Konto i programmet.")
        sys.exit(1)

    begin, end = sync_window()
    logger.info(f"Undersøger perioden {begin:%Y-%m-%d} til {end:%Y-%m-%d} (samme vindue som den almindelige synk).")

    duplicate_groups = find_duplicates(aula_calendar)
    if not duplicate_groups:
        logger.info("Ingen dubletter fundet. Intet at rydde op i.")
        return

    report = build_duplicate_report(duplicate_groups)
    to_delete = [loser for row in report for loser in row["losers"]]

    print()
    print(f"=== Fandt {len(report)} grupper af dubletter, i alt {len(to_delete)} begivenheder der bør slettes ===")
    print()
    for row in report:
        print(f"- \"{row['title']}\" ({row['start']}) — {len(row['losers']) + 1} kopier")
        print(f"    Beholder: id {row['keeper']['id']} (oprettet {row['keeper']['created']})")
        for loser in row["losers"]:
            print(f"    Sletter:  id {loser['id']} (oprettet {loser['created']})")
        print()

    if not args.execute:
        print(f"Dette var kun en rapport ({len(to_delete)} begivenheder ville blive slettet).")
        print("Kør med --execute for faktisk at slette dem:")
        print("    python cleanup_duplicate_events.py --execute")
        return

    answer = input(
        f"Er du sikker på at du vil slette disse {len(to_delete)} dublet-begivenheder fra AULA? "
        f"Dette kan ikke fortrydes. Skriv SLET for at bekræfte: ").strip()
    if answer != "SLET":
        print("Afbrudt — der er ikke slettet noget.")
        return

    deleted, failed = delete_duplicates(aula_calendar, to_delete)
    print()
    print(f"Færdig — {deleted} slettet, {failed} fejlede.")


if __name__ == "__main__":
    main()
