import csv
import logging
import shutil

from secure_storage import protect, unprotect, is_protected

# Tegn der kan blive fortolket som en formel af Excel/LibreOffice, hvis de
# står først i et CSV-felt (CSV-/formel-injektion). Bruges kun ved eksport
# til klartekst-CSV — den interne, krypterede fil rammes ikke af dette.
_FORMULA_TRIGGER_CHARS = ("=", "+", "-", "@", "\t", "\r")


def _csv_safe(value: str) -> str:
    """Undgår at et felt bliver tolket som en formel, når CSV'en åbnes i Excel."""
    if value and value[0] in _FORMULA_TRIGGER_CHARS:
        return "'" + value
    return value


class PeopleCsvManager():
    def __init__(self, csv_file="personer.csv", people_to_ignore="personer_ignorer.csv") -> None:
        self.logger = logging.getLogger('O2A')
        self.__csv_file = csv_file
        self.__ignore_file = people_to_ignore

        self.__people, alias_needs_migration = self.__readFile(csv_file)
        self.__people_to_ignore, ignore_needs_migration = self.__readFile_ignore(people_to_ignore)

        # Migrerer transparent en ældre, ukrypteret fil til krypteret form
        # ved første indlæsning efter opdateringen — ingen synlig forskel
        # for brugeren, ingen handling påkrævet.
        if alias_needs_migration:
            self.__write_alias_file()
        if ignore_needs_migration:
            self.__write_ignore_file()

    # ── Inline-editor API (Personer-siden) ───────────────────────────────────

    def get_ignored_people(self) -> list:
        """Liste af Outlook-navne, der udelades fra synkronisering."""
        return [p["outlook_name"] for p in self.__people_to_ignore]

    def get_aliases(self) -> list:
        """Liste af (outlook_navn, aula_navn)-par."""
        return [(p["outlook_name"], p["aula_name"]) for p in self.__people]

    def add_ignored_person(self, outlook_name: str):
        outlook_name = outlook_name.strip()
        if not outlook_name:
            return
        if any(p["outlook_name"] == outlook_name for p in self.__people_to_ignore):
            return
        self.__people_to_ignore.append({"outlook_name": outlook_name})
        self.__write_ignore_file()

    def remove_ignored_person(self, outlook_name: str):
        self.__people_to_ignore = [
            p for p in self.__people_to_ignore if p["outlook_name"] != outlook_name
        ]
        self.__write_ignore_file()

    def add_alias(self, outlook_name: str, aula_name: str):
        outlook_name = outlook_name.strip()
        aula_name = aula_name.strip()
        if not outlook_name or not aula_name:
            return
        self.__people = [p for p in self.__people if p["outlook_name"] != outlook_name]
        self.__people.append({"outlook_name": outlook_name, "aula_name": aula_name})
        self.__write_alias_file()

    def remove_alias(self, outlook_name: str):
        self.__people = [p for p in self.__people if p["outlook_name"] != outlook_name]
        self.__write_alias_file()

    # ── Eksport / import (klartekst, til manuel bulk-redigering) ────────────

    def export_aliases_to(self, path: str):
        """Eksporterer alias-listen til en klartekst-CSV, fx til redigering i
        Excel. Kaldestedet er ansvarlig for at advare brugeren om, at filen
        ikke er beskyttet som den interne, krypterede liste."""
        with open(path, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Outlook navn", "AULA navn"])
            for p in self.__people:
                writer.writerow([_csv_safe(p["outlook_name"]), _csv_safe(p["aula_name"])])

    def import_aliases_from(self, path: str) -> int:
        """Importerer alias-par fra en CSV-fil i samme format som eksporten.
        Returnerer antal importerede/opdaterede rækker."""
        count = 0
        with open(path, mode='r', encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                outlook_name = (row.get("Outlook navn") or "").strip()
                aula_name = (row.get("AULA navn") or "").strip()
                if outlook_name and aula_name:
                    self.add_alias(outlook_name, aula_name)
                    count += 1
        return count

    def export_ignored_to(self, path: str):
        with open(path, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Outlook navn"])
            for p in self.__people_to_ignore:
                writer.writerow([_csv_safe(p["outlook_name"])])

    def import_ignored_from(self, path: str) -> int:
        count = 0
        with open(path, mode='r', encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                outlook_name = (row.get("Outlook navn") or "").strip()
                if outlook_name:
                    self.add_ignored_person(outlook_name)
                    count += 1
        return count

    # ── Intern, krypteret lagring ─────────────────────────────────────────────

    def __write_ignore_file(self):
        with open(self.__ignore_file, mode="w", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Outlook navn"])
            for p in self.__people_to_ignore:
                writer.writerow([protect(p["outlook_name"])])

    def __write_alias_file(self):
        with open(self.__csv_file, mode="w", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Outlook navn", "AULA navn"])
            for p in self.__people:
                writer.writerow([protect(p["outlook_name"]), protect(p["aula_name"])])

    def getPersonData(self,person_outlook_name):
        self.logger.debug(f"Searching for {person_outlook_name} in CSV register")

        for person in self.__people:
            outlook_name = person["outlook_name"]
            self.logger.debug(f"Sammenligner OUTLOOK NAVN {person_outlook_name} med Registernavn {outlook_name}")
            if person["outlook_name"] == person_outlook_name:
                aula_name = person["aula_name"]
                self.logger.debug(f"FOUND and should be replaced with {aula_name}")
                return aula_name

        for person in self.__people_to_ignore:
            if person["outlook_name"] == person_outlook_name:
                self.logger.debug(f"FOUND and should be IGNORED")
                return "IGNORE_PERSON"

        self.logger.debug("NOT FOUND")
        return None

    def __readFile_ignore(self, csv_file="personer_ignorer.csv"):
        people = []
        needs_migration = False

        try:
            with open(csv_file, mode='r') as csv_file:
                csv_reader = csv.DictReader(csv_file,delimiter=";")
                line_count = 0
                for row in csv_reader:
                    if line_count == 0:
                        self.logger.debug(f'Column names are {"; ".join(row)}')
                        line_count += 1

                    raw_name = row["Outlook navn"]
                    if raw_name and not is_protected(raw_name):
                        needs_migration = True

                    person = {
                        "outlook_name" : unprotect(raw_name),
                    }

                    people.append(person)

                    self.logger.debug(f'\t{row["Outlook navn"]}.')
                    line_count += 1

                self.logger.debug(people)
                self.logger.debug(f'Processed {line_count} lines.')
        except FileNotFoundError as e:
            self.logger.warning(f"CSV filen '{csv_file}'' blev ikke fundet. Prøver at oprette den, og genkøre sig køre igen.")
            self.logger.debug(e)

            shutil.copy2("personer_ignorer_skabelon.csv","personer_ignorer.csv")

            people, needs_migration = self.__readFile_ignore()

        return people, needs_migration

    def __readFile(self, csv_file="personer.csv"):
        people = []
        needs_migration = False

        try:
            with open(csv_file, mode='r') as csv_file:
                csv_reader = csv.DictReader(csv_file,delimiter=";")
                line_count = 0
                for row in csv_reader:
                    if line_count == 0:
                        self.logger.debug(f'Column names are {"; ".join(row)}')
                        line_count += 1

                    raw_outlook_name = row["Outlook navn"]
                    raw_aula_name = row["AULA navn"]
                    if (raw_outlook_name and not is_protected(raw_outlook_name)) or \
                       (raw_aula_name and not is_protected(raw_aula_name)):
                        needs_migration = True

                    person = {
                        "outlook_name" : unprotect(raw_outlook_name),
                        "aula_name" : unprotect(raw_aula_name)
                    }

                    people.append(person)

                    self.logger.debug(f'\t{row["Outlook navn"]} har ALIAS {row["AULA navn"]} .')
                    line_count += 1

                self.logger.debug(people)
                self.logger.debug(f'Processed {line_count} lines.')
        except FileNotFoundError as e:
            self.logger.warning(f"CSV filen '{csv_file}'' blev ikke fundet. Prøver at oprette den, og genkøre sig køre igen.")
            self.logger.debug(e)

            shutil.copy2("personer_skabelon.csv","personer.csv")

            people, needs_migration = self.__readFile()

        return people, needs_migration

#pClass = PeopleCsvManager(csv_file="personer.csv")
#print(pClass.getPersonData("Fiktiv Fiktivsen"))
