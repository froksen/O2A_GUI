# This Python file uses the following encoding: utf-8
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging


_AULA_PORTAL_URL = "https://www.aula.dk"
_BROKER_START_URL = "https://login.aula.dk/auth/login.php?type=unilogin"


class LoginStatus:
    def __init__(self):
        self.status = False
        self.error_messages = []
        self.username = ""


class AulaConnection:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.logger = logging.getLogger('O2A')
        self.__profilesByLogin = ""
        self._api_version = 23

    # ── Profile helpers ────────────────────────────────────────────────────────

    def getProfileId(self):
        profiles = self.getProfilesByLogin()['data']['profiles']
        for profile in profiles:
            if profile['institutionProfiles'][0]['role'] == "employee":
                return profile['institutionProfiles'][0]['id']

    def setProfilesByLogin(self, profile):
        self.__profilesByLogin = profile

    def getProfilesByLogin(self):
        return self.__profilesByLogin

    @property
    def ProfileinstitutionCode(self):
        profiles = self.getProfilesByLogin()['data']['profiles']
        for profile in profiles:
            if profile['institutionProfiles'][0]['role'] == "employee":
                return profile['institutionProfiles'][0]['institutionCode']

    def getAulaApiUrl(self):
        return f'https://www.aula.dk/api/v{self._api_version}/'

    def _detect_api_version(self) -> None:
        """Finder den aktuelle Aula API-version automatisk fra portalens kildekode."""
        try:
            response = self.session.get(_AULA_PORTAL_URL + "/portal/", timeout=10)
            match = re.search(r'/api/v(\d+)/', response.text)
            if match:
                self._api_version = int(match.group(1))
                self.logger.info("Aula API-version fundet: v%d", self._api_version)
                return

            # Ikke fundet i HTML — søg i app/main JS-bundlefiler
            soup = BeautifulSoup(response.text, "html.parser")
            for script in soup.find_all("script", src=re.compile(r'(app|main|chunk)\.')):
                src = script["src"]
                if not src.startswith("http"):
                    src = _AULA_PORTAL_URL + src
                try:
                    js_resp = self.session.get(src, timeout=15)
                    match = re.search(r'/api/v(\d+)/', js_resp.text)
                    if match:
                        self._api_version = int(match.group(1))
                        self.logger.info("Aula API-version fundet i bundle: v%d", self._api_version)
                        return
                except Exception:
                    continue

            self.logger.warning("Aula API-version ikke fundet — bruger v%d som fallback", self._api_version)
        except Exception as e:
            self.logger.warning("Fejl ved API-versiondetektering: %s — bruger v%d", e, self._api_version)

    def getSession(self):
        return self.session

    # ── Public login entry point ───────────────────────────────────────────────

    def login(self, username: str, password: str, idp_id: str | None = None) -> LoginStatus:
        """Log in to Aula.

        idp_id: selectedIdp value from aula.idp_config.LOCAL_IDPS, or None for
                standard UniLogin (STIL).
        """
        if idp_id:
            return self.login_with_local_idp(username, password, idp_id)
        return self.login_with_stil(username, password)

    # ── Local IDP login (Lokalt login / OS2faktor / kommunal IDP) ─────────────

    def login_with_local_idp(self, username: str, password: str, idp_id: str) -> LoginStatus:
        """Log in via the UniLogin broker's 'Lokalt login' flow.

        Flow:
          1. GET broker start page  (login.aula.dk → broker.unilogin.dk)
          2. POST selectedIdp=<idp_id> to broker form
          3. Generic form-chain until Aula portal (handles SAML redirects +
             the OS2faktor username/password form)
        """
        login_response = LoginStatus()
        login_response.username = username
        session = self.getSession()

        # ── Step 1: broker start page ──────────────────────────────────────────
        self.logger.info("Lokalt login: henter UniLogin broker-side…")
        try:
            response = session.get(_BROKER_START_URL)
        except requests.exceptions.ConnectionError as e:
            self.logger.critical("Ingen forbindelse til UniLogin: %s", e)
            login_response.error_messages.append("Ingen forbindelse til UniLogin-brokeren")
            return login_response

        soup = BeautifulSoup(response.text, "html.parser")
        broker_form = soup.find("form")
        if not broker_form:
            self.logger.critical("Lokalt login: broker-formular ikke fundet")
            login_response.error_messages.append("Broker-formular ikke fundet")
            return login_response

        # ── Step 2: vælg lokal IDP direkte ────────────────────────────────────
        self.logger.info("Lokalt login: vælger IDP '%s'…", idp_id)
        response = session.post(broker_form["action"], data={"selectedIdp": idp_id})

        # ── Step 3: generisk formular-kæde ────────────────────────────────────
        return self._follow_form_chain(response, session, username, password, login_response)

    # ── Standard UniLogin (STIL) login ────────────────────────────────────────

    def login_with_stil(self, username: str, password: str) -> LoginStatus:
        """Log in via standard UniLogin (uni_idp) — for STIL-brugere."""
        login_response = LoginStatus()
        login_response.username = username
        session = self.getSession()

        self.logger.info("UniLogin STIL: henter broker-side…")
        try:
            response = session.get(_BROKER_START_URL)
        except requests.exceptions.ConnectionError as e:
            self.logger.critical("Ingen forbindelse til UniLogin: %s", e)
            login_response.error_messages.append("Ingen forbindelse til UniLogin-brokeren")
            return login_response

        soup = BeautifulSoup(response.text, "html.parser")
        broker_form = soup.find("form")
        if not broker_form:
            login_response.error_messages.append("Broker-formular ikke fundet")
            return login_response

        self.logger.info("UniLogin STIL: vælger uni_idp…")
        response = session.post(broker_form["action"], data={"selectedIdp": "uni_idp"})

        return self._follow_form_chain(response, session, username, password, login_response)

    # ── Shared form-chain helper ───────────────────────────────────────────────

    def _follow_form_chain(self, response, session, username: str, password: str,
                           login_response: LoginStatus) -> LoginStatus:
        """Follow SAML/login form redirects until the Aula portal URL is reached.

        Handles:
        - OS2faktor 'Brugerkonto' form  (fields: _csrf, username, password)
        - UniLogin credential form      (fields: username, password, selected-aktoer)
        - SAML POST-binding forms       (fields: SAMLResponse, RelayState, …)
        - Relative form actions         → resolved against current response URL
        """
        self.logger.info("Forsøger at logge på Aula…")

        for step in range(15):
            if response.url.startswith(_AULA_PORTAL_URL + ":443/portal/") or \
               response.url.startswith(_AULA_PORTAL_URL + "/portal/"):
                return self._finalize_login(session, login_response)

            soup = BeautifulSoup(response.text, "html.parser")
            form = soup.find("form")
            if not form:
                self.logger.warning("Ingen formular fundet på trin %d (URL: %s)", step, response.url)
                break

            action = form.get("action", "")
            if not action:
                self.logger.warning("Tom form-action på trin %d", step)
                break

            # Gør relativ URL absolut
            if action.startswith("/"):
                parsed = urlparse(response.url)
                action = f"{parsed.scheme}://{parsed.netloc}{action}"

            # Tjek for synlige login-fejl
            for err_span in soup.find_all("span", {"class": "form-error-message"}):
                msg = err_span.get_text(strip=True)
                self.logger.critical("Login-fejlmeddelelse: %s", msg)
                login_response.error_messages.append(msg)
                login_response.status = False
                return login_response

            # Saml inputs fra FØRSTE formular
            data = {}
            for inp in form.find_all("input"):
                name = inp.get("name")
                if not name:
                    continue
                if name == "username":
                    data[name] = username
                    self.logger.debug("Login-felt: username")
                elif name == "password":
                    data[name] = password
                    self.logger.debug("Login-felt: password")
                elif name == "selected-aktoer":
                    data[name] = "MEDARBEJDER_EKSTERN"
                    self.logger.debug("Login-felt: selected-aktoer → MEDARBEJDER_EKSTERN")
                else:
                    data[name] = inp.get("value") or ""

            response = session.post(action, data=data)

        # Kom ikke frem til portalen inden max trin
        self.logger.critical("Login mislykkedes efter gennemgang af formular-kæden")
        login_response.status = False
        return login_response

    def _finalize_login(self, session, login_response: LoginStatus) -> LoginStatus:
        """Henter profil og sætter CSRF-token efter succesfuldt login."""
        self.logger.info("Login var succesfuldt!")
        self._detect_api_version()
        try:
            params = {"method": "profiles.getProfilesByLogin"}
            profile = session.get(self.getAulaApiUrl(), params=params).json()
            self.setProfilesByLogin(profile)
            session.headers["csrfp-token"] = session.cookies["Csrfp-Token"]
            login_response.status = True
        except Exception as e:
            self.logger.critical("Fejl ved hentning af profil efter login: %s", e)
            login_response.status = False
            login_response.error_messages.append("Profil kunne ikke hentes efter login")
        return login_response
