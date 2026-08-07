"""
Diagnostisk script:
1. Opretter testbegivenhed i Outlook (18:00-18:30, kategori: AULA)
2. Læser den tilbage og viser rå datetime-værdier og tzinfo
3. Viser hvad koden vil sende til AULA
"""

import win32com.client
import datetime as dt
from datetime import timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from aula.timezone_utils import format_aula_datetime, ensure_local_copenhagen_datetime

# ---- Opret testbegivenhed i Outlook ----
outlook = win32com.client.Dispatch("Outlook.Application")
ns = outlook.GetNamespace("MAPI")

cal = ns.GetDefaultFolder(9)

appointment = outlook.CreateItem(1)  # olAppointmentItem
appointment.Subject = "test"
appointment.Categories = "AULA"

# Sæt dato til i dag kl. 18:00-18:30
today = dt.date.today()
start = dt.datetime(today.year, today.month, today.day, 18, 0, 0)
end   = dt.datetime(today.year, today.month, today.day, 18, 30, 0)

appointment.Start = start
appointment.End   = end
appointment.Save()

print(f"Testbegivenhed oprettet: '{appointment.Subject}'")
print(f"  Python dt sendt til Outlook.Start : {start}  (tzinfo={start.tzinfo})")
print()

# ---- Læs den tilbage ----
items = cal.Items
items.IncludeRecurrences = False
items.Sort("[Start]")

restrict_begin = today.strftime('%d/%m/%Y')
restrict_end   = (today + timedelta(days=1)).strftime('%d/%m/%Y')
restriction = f"[Start] >= '{restrict_begin}' AND [END] <= '{restrict_end}'"
filtered = items.Restrict(restriction)

for ev in filtered:
    if ev.Subject == "test":
        raw_start = ev.Start
        raw_end   = ev.End
        print("=== Rå værdier fra win32com ===")
        print(f"  ev.Start        : {raw_start}")
        print(f"  type(ev.Start)  : {type(raw_start)}")
        print(f"  ev.Start.tzinfo : {raw_start.tzinfo}")
        print()

        # Hvad koden gør i dag:
        converted_start = ensure_local_copenhagen_datetime(raw_start)
        converted_end   = ensure_local_copenhagen_datetime(raw_end)
        formatted_start = format_aula_datetime(raw_start)
        formatted_end   = format_aula_datetime(raw_end)

        print("=== Efter ensure_local_copenhagen_datetime ===")
        print(f"  start → {converted_start}")
        print(f"  end   → {converted_end}")
        print()
        print("=== Hvad der sendes til AULA (startDateTime / endDateTime) ===")
        print(f"  startDateTime : {formatted_start}")
        print(f"  endDateTime   : {formatted_end}")
        print()

        # Foreslået fix: behandl som naiv (lokal) tid
        naive_start = raw_start.replace(tzinfo=None)
        naive_end   = raw_end.replace(tzinfo=None)
        fixed_start = format_aula_datetime(naive_start)
        fixed_end   = format_aula_datetime(naive_end)

        print("=== Med foreslået fix (strip tzinfo → treat as local Copenhagen time) ===")
        print(f"  startDateTime : {fixed_start}")
        print(f"  endDateTime   : {fixed_end}")
        print()
        break
else:
    print("FEJL: Testbegivenheden 'test' blev ikke fundet i kalenderen!")
