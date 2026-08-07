import contextlib
import configparser
import time
from pathlib import Path

import keyring
import win32com.client

# Synkroniseringsadfærd — valgmuligheder vist i Indstillinger (key, label)
SYNC_BEHAVIOR_OPTIONS = [
    ("aula_only", "Overfør kun begivenheder med kategorien 'AULA'"),
    (
        "aula_busy_fallback",
        "Overfør optaget status. Begivenheder med kategorien 'AULA' "
        "overføres med alle detaljer",
    ),
    ("all_direct", "Overfør alle begivenheder med alle detaljer"),
]

_CONFIG_PATH = "configuration.ini"


class SetupManager:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.__read_config_file()

    def update_unilogin(self, username, password, idp_id: str = ""):
        with contextlib.suppress(configparser.DuplicateSectionError):
            self.config.add_section("AULA")

        self.config["AULA"]["username"] = username
        self.config["AULA"]["idp_id"] = idp_id
        keyring.set_password("o2a", "aula_password", password)
        self.__write_config_file()

    def get_aula_idp_id(self) -> str:
        try:
            return self.config["AULA"].get("idp_id", "") or ""
        except KeyError:
            return ""

    def set_hide_on_startup(self, value: str):
        with contextlib.suppress(configparser.DuplicateSectionError):
            self.config.add_section("GUI")

        self.config["GUI"]["hideonstartup"] = value
        self.__write_config_file()

    def hide_on_startup(self):
        with contextlib.suppress(configparser.DuplicateSectionError):
            self.config.add_section("GUI")

        return self.config["GUI"].getboolean("hideonstartup", False)

    def create_outlook_categories(self):
        outlook = win32com.client.Dispatch("Outlook.Application")
        ns = outlook.GetNamespace("MAPI")

        print("Checking if Outlook has necessary categories")
        has_aula = False
        has_aula_institutionskalender = False
        for category in ns.Categories:
            if category.name == "AULA":
                has_aula = True

            if category.name == "AULA Institutionskalender":
                has_aula_institutionskalender = True

        if not has_aula:
            print("Missing category 'AULA'. Will be created")
            ns.Categories.Add("AULA")
            time.sleep(1)  # needed because otherwise outlook can keep up.

        if not has_aula_institutionskalender:
            print("Missing category 'AULA Institutionskalender'. Will be created")
            ns.Categories.Add("AULA Institutionskalender")
            time.sleep(1)  # needed because otherwise outlook can keep up.

        if has_aula_institutionskalender and has_aula:
            print("All necessary categories was found.")

    def get_aula_username(self):
        return self.config["AULA"]["username"]

    def get_aula_password(self):
        return keyring.get_password("o2a", "aula_password")

    def get_sync_behavior(self) -> str:
        try:
            return self.config["SYNC"].get("behavior", SYNC_BEHAVIOR_OPTIONS[0][0])
        except KeyError:
            return SYNC_BEHAVIOR_OPTIONS[0][0]

    def set_sync_behavior(self, value: str):
        with contextlib.suppress(configparser.DuplicateSectionError):
            self.config.add_section("SYNC")

        self.config["SYNC"]["behavior"] = value
        self.__write_config_file()

    def get_last_run(self):
        try:
            return self.config["SYNC"].get("last_run") or None
        except KeyError:
            return None

    def set_last_run(self, timestamp: str):
        with contextlib.suppress(configparser.DuplicateSectionError):
            self.config.add_section("SYNC")
        self.config["SYNC"]["last_run"] = timestamp
        self.__write_config_file()

    def __read_config_file(self):
        if not Path(_CONFIG_PATH).is_file():
            self.update_unilogin("Ukendt", "Ukendt")

        with contextlib.suppress(Exception):
            self.config.read(_CONFIG_PATH)

    def __write_config_file(self):
        with Path(_CONFIG_PATH).open("w") as configfile:
            self.config.write(configfile)
