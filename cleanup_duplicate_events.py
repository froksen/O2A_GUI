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
import time

from dateutil.relativedelta import relativedelta, SU

from setupmanager import SetupManager
from aula import AulaCalendar, AulaConnection

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("cleanup_duplicate_events")
logging.getLogger("O2A").setLevel(logging.WARNING)  # dæmp AulaCalendars egen logger her


def _sync_window():
    """Samme datovindue som den almindelige synk bruger (mainwindow.update_calendar)."""
    today = dt.datetime.today()
    last_sunday = today + relativedelta(weekday=SU(-1))
    begin = dt.datetime(last_sunday.year, last_sunday.month, last_sunday.day, 1, 0, 0)
    end = dt.datetime(today.year + 1, 7, 1, 0, 0, 0)
    return begin, end


def fetch_own_events_raw(aula_calendar: AulaCalendar, begin: dt.datetime, end: dt.datetime):
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

        logger.info(f"Henter begivenheder fra {start_text} til {end_text}…")
        raw_events += aula_calendar.getEventsByProfileIdsAndResourceIds(
            aula_calendar._profile_id, start_text, end_text)

    return raw_events


def group_by_outlook_id(aula_calendar: AulaCalendar, raw_events: list):
    """Henter fulde detaljer for hver rå begivenhed og grupperer dem efter
    deres Outlook GlobalAppointmentID-vandmærke. Begivenheder uden vandmærke
    (ikke oprettet af O2A) sorteres fra."""
    groups = collections.defaultdict(list)
    seen_ids = set()
    total = len(raw_events)

    for i, event in enumerate(raw_events, start=1):
        event_id = event["id"]
        if event_id in seen_ids:
            continue  # samme begivenhed kan optræde i flere måneders vindue ved kant-overlap
        seen_ids.add(event_id)

        if i % 25 == 0 or i == total:
            logger.info(f"Læser begivenhedsdetaljer… ({i} af {total})")

        response = aula_calendar.getEventById(event_id)
        if not response or not response.get("data"):
            logger.warning(f"Kunne ikke hente detaljer for begivenhed {event_id} — springer over.")
            continue

        data = response["data"]
        description = data["description"]["html"]
        global_id, _lmt = aula_calendar._parse_o2a_watermark(description)
        if not global_id:
            continue  # ikke oprettet af O2A — rør den ikke

        groups[global_id].append({
            "id": event_id,
            "title": data.get("title"),
            "start": data.get("startDateTime"),
            "created": data.get("createdDateTime"),
        })

        # Kaldene køres sekventielt (ikke samtidigt) med en lille pause, netop
        # for ikke selv at genskabe den rate-limit-situation der forårsagede
        # dubletterne i første omgang — se getEventById i aula_calendar.py.
        time.sleep(0.1)

    return groups


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--execute", action="store_true",
                        help="Slet faktisk de fundne dubletter. Uden dette flag laves kun en rapport.")
    args = parser.parse_args()

    setupmgr = SetupManager()
    username = setupmgr.get_aula_username()
    password = setupmgr.get_aula_password()
    idp_id = setupmgr.get_aula_idp_id()

    if not setupmgr.is_aula_configured():
        logger.error("AULA-login er ikke konfigureret endnu. Kør programmet og gennemfør opsætningen først.")
        sys.exit(1)

    logger.info("Logger ind i AULA…")
    aula_connection = AulaConnection()
    login_status = aula_connection.login(username, password, idp_id=idp_id or None)
    if not login_status.status:
        logger.error("Login mislykkedes — tjek dine loginoplysninger under Konto i programmet.")
        sys.exit(1)

    aula_calendar = AulaCalendar(aula_connection=aula_connection)

    begin, end = _sync_window()
    logger.info(f"Undersøger perioden {begin:%Y-%m-%d} til {end:%Y-%m-%d} (samme vindue som den almindelige synk).")

    raw_events = fetch_own_events_raw(aula_calendar, begin, end)
    logger.info(f"Fandt {len(raw_events)} egne begivenheder i alt. Henter detaljer for at finde dubletter…")

    groups = group_by_outlook_id(aula_calendar, raw_events)
    duplicate_groups = {k: v for k, v in groups.items() if len(v) > 1}

    if not duplicate_groups:
        logger.info("Ingen dubletter fundet. Intet at rydde op i.")
        return

    total_to_delete = sum(len(v) - 1 for v in duplicate_groups.values())
    print()
    print(f"=== Fandt {len(duplicate_groups)} grupper af dubletter, i alt {total_to_delete} begivenheder der bør slettes ===")
    print()

    to_delete = []
    for global_id, members in duplicate_groups.items():
        members_sorted = sorted(members, key=lambda m: m["id"])  # laveste id = ældst = beholdes
        keeper = members_sorted[0]
        losers = members_sorted[1:]

        title = keeper["title"] or "(uden titel)"
        start = keeper["start"] or "?"
        print(f"- \"{title}\" ({start}) — {len(members_sorted)} kopier")
        print(f"    Beholder: id {keeper['id']} (oprettet {keeper['created']})")
        for loser in losers:
            print(f"    Sletter:  id {loser['id']} (oprettet {loser['created']})")
            to_delete.append(loser)
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

    deleted, failed = 0, 0
    for i, loser in enumerate(to_delete, start=1):
        logger.info(f"Sletter ({i} af {len(to_delete)}): \"{loser['title']}\" — id {loser['id']}")
        if aula_calendar.deleteEvent(loser["id"]):
            deleted += 1
        else:
            failed += 1
            logger.warning(f"Kunne ikke slette begivenhed {loser['id']}.")

    print()
    print(f"Færdig — {deleted} slettet, {failed} fejlede.")


if __name__ == "__main__":
    main()
