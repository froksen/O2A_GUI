from aula.aula_event import AulaEvent
import datetime
from dateutil.relativedelta import relativedelta
import logging
from .aula_connection import AulaConnection
from .utils import calculate_day_of_the_week_mask, teams_url_fixer
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from peoplecsvmanager import PeopleCsvManager
import requests
import json
from .timezone_utils import format_aula_datetime


class AulaCalendar:
    def __init__(self, aula_connection: AulaConnection):
        self._aula_api_url = aula_connection.getAulaApiUrl()
        self._session = aula_connection.getSession()
        self._profile_id = aula_connection.getProfileId()
        self._profile_institution_code = aula_connection.ProfileinstitutionCode

        # Sets logger
        self.logger = logging.getLogger("O2A")

        # Cache for recipient IDs so the same person isn't looked up more than once
        self._recipient_cache = {}

    def __remove_html_tags(self, text):
        """Remove html tags from a string"""
        import re

        clean = re.compile("<.*?>")
        return re.sub(clean, "", text)

    def convert_outlook_appointmentitem_to_aula_event(self, outlookobject) -> AulaEvent:

        # Read more about patterns: https://docs.microsoft.com/en-us/dotnet/api/microsoft.office.interop.outlook.olrecurrencetype?view=outlook-pia
        def outlook_pattern_to_aula_pattern(x):
            x = int(x)
            return {0: "daily", 1: "weekly", 2: "monthly"}.get(x, "never")

        aula_event = AulaEvent()

        # "Optaget"-placeholder (aula_busy_fallback): kun titlen må afsløre at tiden er optaget —
        # beskrivelse, lokation og deltagere skjules så begivenhedens indhold ikke lækkes.
        is_busy_placeholder = bool(outlookobject.get("aula_title_override"))

        aula_event.id = ""
        aula_event.outlook_global_appointment_id = outlookobject[
            "outlook_GlobalAppointmentID_internal"
        ]  # outlookobject["appointmentitem"].GlobalAppointmentID #outlookobject["outlook_GlobalAppointmentID_internal"]
        aula_event.outlook_organizer = outlookobject["appointmentitem"].Organizer
        aula_event.institution_code = ""
        aula_event.creator_inst_profile_id = ""
        aula_event.title = (
            outlookobject.get("aula_title_override")
            or outlookobject["appointmentitem"].subject
        )
        aula_event.type = "event"
        aula_event.outlook_body = (
            "" if is_busy_placeholder else outlookobject["appointmentitem"].body
        )
        aula_event.location = (
            "" if is_busy_placeholder else outlookobject["appointmentitem"].location
        )
        aula_event.start_date = outlookobject["aula_startdate"]
        aula_event.end_date = outlookobject["aula_enddate"]
        aula_event.start_time = outlookobject["aula_starttime"]
        aula_event.end_time = outlookobject["aula_endtime"]
        aula_event.start_timezone = outlookobject["aula_startdate_timezone"]
        aula_event.end_timezone = outlookobject["aula_enddate_timezone"]
        aula_event.outlook_last_modification_time = outlookobject[
            "appointmentitem"
        ].LastModificationTime
        aula_event.all_day = outlookobject["appointmentitem"].AllDayEvent
        aula_event.private = (
            True if outlookobject["appointmentitem"].Sensitivity == 2 else False
        )  # Værdien 2 betyder privat
        aula_event.is_recurring = outlookobject["appointmentitem"].IsRecurring
        aula_event.hide_in_own_calendar = outlookobject["hideInOwnCalendar"]
        aula_event.add_to_institution_calendar = outlookobject[
            "addToInstitutionCalendar"
        ]
        aula_event.is_private = (
            True if outlookobject["appointmentitem"].Sensitivity == 2 else False
        )  # Værdien 2 betyder privat
        aula_event.outlook_required_attendees = (
            []
            if is_busy_placeholder
            else outlookobject["appointmentitem"].RequiredAttendees.split(";")
        )
        aula_event.interval = (
            outlookobject["appointmentitem"].GetRecurrencePattern().Interval
        )
        aula_event.recurrence_pattern = outlookobject[
            "appointmentitem"
        ].GetRecurrencePattern()
        aula_event.max_date = str(
            outlookobject["appointmentitem"].GetRecurrencePattern().PatternEndDate
        ).split(" ")[
            0
        ]  # Only the date part is needed. EX: 2022-02-11 00:00:00+00:00 --> 2022-02-11
        aula_event.aula_recurrence_pattern = outlook_pattern_to_aula_pattern(
            outlookobject["appointmentitem"].GetRecurrencePattern().RecurrenceType
        )
        aula_event.day_of_week_mask_list = self.get_day_of_the_week_mask(
            outlookobject["appointmentitem"].GetRecurrencePattern().DayOfWeekMask
        )
        aula_event.response_required = outlookobject[
            "appointmentitem"
        ].ResponseRequested

        return aula_event

    def get_day_of_the_week_mask(self, day_mask_sum):
        days_combinations = calculate_day_of_the_week_mask()

        for day in days_combinations:
            if day_mask_sum == day["sum"]:
                return day["days_integer"]

        return False

    def find_recipient_alias(self, recipient_name) -> str:
        peoplecsvmanager = PeopleCsvManager()

        csv_aula_name = peoplecsvmanager.getPersonData(recipient_name)

        self.logger.debug(f"      Undersøger om personen {recipient_name} har et ALIAS")
        self.logger.debug(csv_aula_name)
        if csv_aula_name is not None:
            self.logger.info(
                "      OBS: Deltagerens %s Outlook navn blev fundet i CSV-filen og blev erstattet med %s"
                % (recipient_name, csv_aula_name)
            )
            return csv_aula_name

        return recipient_name

    def should_ignore_recipient(self, recipient_name) -> bool:
        csv_aula_name = PeopleCsvManager().getPersonData(recipient_name)
        if csv_aula_name == "IGNORE_PERSON":
            self.logger.info(
                "      OBS: Deltagerens %s Outlook navn blev fundet i IGNORER-filen og vil derfor ikke blive tilføjet til begivenheden"
                % (recipient_name)
            )
            return True

        return False

    def get_atendees_ids(self, event: AulaEvent):
        for attendee in event.outlook_required_attendees:
            attendee = str(attendee).strip()
            attendee = attendee.split("(")[
                0
            ].strip()  # Fjerner potentielle mailadresser i navne

            self.logger.info('     Søger efter deltageren "%s" på AULA.' % (attendee))

            if attendee == str(event.outlook_organizer) or attendee == "":
                self.logger.info("     Deltageren er arrangør - Springer over")
                continue

            # Finder eventuelt alias som personen har
            attendee = self.find_recipient_alias(attendee)

            # Om personen skal ignoreres eller ej.
            if self.should_ignore_recipient(attendee) or attendee == "IGNORE_PERSON":
                self.logger.info(
                    "     OBS: Deltagerens blev fundet i IGNORER-filen - Springer over"
                )
                continue

            # Slår personen op på AULA, og får ID'et herfra.
            search_for_recipient_attempts = 1
            search_for_recipient_attempts_max = 2

            attendee_found = False
            while (
                search_for_recipient_attempts <= search_for_recipient_attempts_max
                and not attendee_found
            ):
                search_result = "Blev ikke fundet."
                attendee_id = self.findRecipient(attendee)
                if attendee_id is not None:
                    event.attendee_ids.append(attendee_id)
                    attendee_found = True
                    search_result = "Blev fundet. Undlader at prøve igen."
                    self.logger.info(
                        f"       (Forsøg {search_for_recipient_attempts} af {search_for_recipient_attempts_max} : {search_result}"
                    )
                    break  # Found — no need to sleep or retry

                self.logger.info(
                    f"       (Forsøg {search_for_recipient_attempts} af {search_for_recipient_attempts_max} : {search_result}"
                )

                if search_for_recipient_attempts == 2 and attendee_id is None:
                    event.creation_or_update_errors.attendees_not_found.append(attendee)

                search_for_recipient_attempts = search_for_recipient_attempts + 1
                time.sleep(1)  # Only sleep before a retry, not after a successful find

        return event

    def findRecipient(self, recipient_name):

        if recipient_name in self._recipient_cache:
            self.logger.info(f'     Deltager "{recipient_name}" fundet i cache.')
            return self._recipient_cache[recipient_name]

        params = {
            "method": "search.findRecipients",
            "text": recipient_name,
            "query": recipient_name,
            "id": str(self._profile_id),
            "typeahead": "true",
            "limit": "100",
            "scopeEmployeesToInstitution": "true",
            "instCode": str(self._profile_institution_code),
            "fromModule": "event",
            "docTypes[]": "Profile",
            "docTypes[]": "Group",
        }

        # url = " https://www.aula.dk/api/v11/?method=search.findRecipients&text=Stefan&query=Stefan&id=779467&typeahead=true&limit=100&scopeEmployeesToInstitution=false&fromModule=event&instCode=537007&docTypes[]=Profile&docTypes[]=Group"
        url = (
            self._aula_api_url
            + "?method=search.findRecipients&text="
            + recipient_name
            + "&query="
            + recipient_name
            + "&id="
            + str(self._profile_id)
            + "&typeahead=true&limit=100&scopeEmployeesToInstitution=true&fromModule=event&instCode="
            + str(self._profile_institution_code)
            + "&docTypes[]=Profile&docTypes[]=Group"
        )

        response = self._session.get(url, params=params).json()
        # response = session.get(url).json()
        # print(json.dumps(response, indent=4))
        recipient_profileid = -1
        try:
            for result in response["data"]["results"]:
                if result["portalRole"] == "employee":
                    recipient_profileid = result[
                        "docId"
                    ]  # Appearenly its docId and not profileId
                    self._recipient_cache[recipient_name] = int(recipient_profileid)
                    return int(recipient_profileid)

        except Exception as e:
            self.logger.warning(f"Kunne ikke slå deltager op ({recipient_name}): {e}")
            return None

    def deleteEvent(self, eventId):
        session = self._session
        url = self._aula_api_url

        params = {"method": "calendar.deleteEvent"}

        data = {"id": eventId}

        response = session.post(url, params=params, json=data).json()
        # print(json.dumps(response, indent=4))

        if response["status"]["message"] == "OK":
            # self.logger.info("Begivenheden blev fjernet!")
            return True
        self.logger.warning("Begivenheden blev IKKE fjernet!")
        return False

    def updateEvent(self, aula_event):
        session = self._session
        url = self._aula_api_url

        params = {"method": "calendar.updateSimpleEvent"}

        aula_event.description = teams_url_fixer(f"{aula_event.description}")

        data = {
            "creator": {"id": self._profile_id},
            "institutionCode": self._profile_institution_code,
            "description": aula_event.description,
            "primaryResource": {},
            "additionalResourceText": aula_event.location,
            "additionalResources": [],
            "invitees": [],
            "invitedGroups": [],
            "attachments": [],
            "pendingMedia": False,
            "timeSlot": None,
            "vacationRegistration": None,
            "isDeleted": False,
            "eventClass": "basic",
            "responseDeadline": None,
            "isDeadlineExceeded": False,
            "addToInstitutionCalendar": aula_event.add_to_institution_calendar,
            "hideInOwnCalendar": aula_event.hide_in_own_calendar,
            "invitedGroupHomeChildren": [],
            "id": aula_event.id,
            "title": aula_event.title,
            "allDay": aula_event.all_day,
            "startDateTime": aula_event.start_date_time,  # "2021-10-03T10:10:00.0000+02:00",
            "endDateTime": aula_event.end_date_time,  # "2021-10-03T12:00:00.0000+02:00",
            # "oldEndDateTime":"2021-10-03T10:00:00+00:00",
            # "oldStartDateTime":"2021-10-03T01:10:00+00:00",
            "responseRequired": aula_event.response_required,
            "private": aula_event.is_private,
            "type": "event",
            "addedToInstitutionCalendar": False,
            # "start":"2021-10-03T01:10:00+00:00",
            # "end":"2021-10-03T10:00:00+00:00",
            "invitedGroupHomes": [],
            "additionalLocations": [],
            "resources": [],
            "pattern": "never",
            "occurenceLimit": 0,
            "weekdayMask": [False, False, False, False, False, False, False],
            "maxDate": None,
            "interval": 0,
            "eventId": aula_event.id,
            "isPrivate": aula_event.is_private,
            "inviteeIds": aula_event.attendee_ids,  # [],
            "invitedGroupIds": [],
            "resourceIds": [],
            "additionalLocationIds": [],
            "additionalResourceIds": [],
            "attachmentIds": [],
            "isEditEvent": True,
        }

        response_calendar = session.post(
            url, params=params, json=data, timeout=10
        ).json()
        # print(json.dumps(response_calendar, indent=4))

        try:
            if response_calendar["status"]["message"] == "OK":
                self.logger.info(
                    'Begivenheden "%s" med start dato %s blev opdateret.'
                    % (aula_event.title, aula_event.start_date_time)
                )
                return True
            self.logger.warning(
                'Begivenheden "%s" med start dato %s blev IKKE opdateret'
                % (aula_event.title, aula_event.start_date_time)
            )
            return False
        except requests.exceptions.Timeout as errt:
            self.logger.info(
                "(TIMEOUT) Begivenheden blev ikke opdateret, grundet manglende svar fra AULA"
            )
            self.logger.debug(errt)
            return None

    def createSimpleEvent(self, aula_event: AulaEvent) -> str | str:

        session = self._session

        # print("START: %s" %(startDateTime))
        # print("END: %s" %(endDateTime))
        # return

        # All API requests go to the below url
        # Each request has a number of parameters, of which method is always included
        # Data is returned in JSON
        url = self._aula_api_url

        ### First example API request ###
        params = {"method": "calendar.createSimpleEvent"}

        description = teams_url_fixer(f"{aula_event.description}")

        data = {
            "title": aula_event.title,
            "description": description,
            "startDateTime": aula_event.start_date_time,  # 2021-05-18T14:30:00.0000+02:00
            "endDateTime": aula_event.end_date_time,  # '2021-05-18T15:00:00.0000+02:00'
            "startDate": datetime.datetime.today().strftime(
                "%Y-%m-%d"
            ),  # Is always today
            "endDate": datetime.datetime.today().strftime(
                "%Y-%m-%d"
            ),  # is always today
            #'startTime': '12:00:19',
            #'endTime': '12:30:19',
            "id": "",
            "institutionCode": self._profile_institution_code,
            "creatorInstProfileId": self._profile_id,
            "type": "event",
            "allDay": aula_event.all_day,
            "private": aula_event.is_private,
            "primaryResource": {},
            "additionalResourceText": aula_event.location,
            "additionalLocations": [],
            "invitees": [],
            "invitedGroups": [],
            "invitedGroupIds": [],
            "invitedGroupHomes": [],
            "responseRequired": True,  # aula_event.response_required, #TODO: Gøre dette på en bedre måde. Lige nu gennemtvunget at der skal spørges efter svar på AULA uanset indstilling i Outlook
            "responseDeadline": None,
            "resources": [],
            "attachments": [],
            "oldStartDateTime": "",
            "oldEndDateTime": "",
            "isEditEvent": False,
            "addToInstitutionCalendar": aula_event.add_to_institution_calendar,
            "hideInOwnCalendar": aula_event.hide_in_own_calendar,
            "inviteeIds": aula_event.attendee_ids,
            "additionalResources": [],
            "pattern": "never",
            "occurenceLimit": 0,
            "weekdayMask": [False, False, False, False, False, False, False],
            "maxDate": None,
            "interval": 0,
            "lessonId": "",
            "noteToClass": "",
            "noteToSubstitute": "",
            "eventId": "",
            "isPrivate": aula_event.is_private,
            "resourceIds": [],
            "additionalLocationIds": [],
            "additionalResourceIds": [],
            "attachmentIds": [],
        }

        try:
            response_calendar = session.post(
                url, params=params, json=data, timeout=10
            ).json()
            # print(json.dumps(response_calendar, indent=4))

            if response_calendar["status"]["message"] == "OK":
                #    self.logger.info("Begivenheden \"%s\" med startdato %s blev oprettet." %(aula_event.title,aula_event.start_date_time))
                aula_event_id = response_calendar["data"]["data"]
                return aula_event_id, "SUCCESS"
            #    self.logger.warning("Begivenheden \"%s\" med startdato %s blev IKKE oprettet." %(aula_event.title,aula_event.start_date_time))
            json_response_dump = json.dumps(response_calendar, indent=4)
            return None, json_response_dump
        except requests.exceptions.Timeout as errt:
            self.logger.info(
                "(TIMEOUT) Begivenheden blev ikke oprettet, grundet manglende svar fra AULA"
            )
            self.logger.debug(errt)
            return None, errt

    def _format_lookup_datetime(self, local_dt):
        return format_aula_datetime(local_dt)

    def getEvents(self, startDatetime, endDatetime, progress_callback=None):

        # Calculates the diffence between the dates.
        monthsDiff = abs(endDatetime.year - startDatetime.year) * 12 + abs(
            endDatetime.month - startDatetime.month
        )

        # Makes sure that even if only one event in same month, the loop will be run
        if monthsDiff <= 0:
            monthsDiff = 1

        events = []
        self.logger.info("Læser AULA kalendere")
        self.logger.info("Lokaliserer begivenheder i kalendere")
        step = 0
        for months in range(monthsDiff):
            lookUp_begin = startDatetime + relativedelta(months=months)
            lookUp_end = startDatetime + relativedelta(months=months + 1)

            # End date can not be later than end date specified.
            if lookUp_end >= endDatetime:
                lookUp_end = endDatetime

            # outlookevents_from_aula = self.icalmanager.readAulaCalendarEvents()
            startTimeFormattet = self._format_lookup_datetime(lookUp_begin)
            endTimeFormattet = self._format_lookup_datetime(lookUp_end)

            step = step + 1

            self.logger.info(
                "  (%i af %i) Begivenheder fra %s til %s"
                % (step, monthsDiff, startTimeFormattet, endTimeFormattet)
            )

            # Includes institution
            self.logger.info("      I institution kalender")
            events = events + self.getEventsForInstitutions(
                self._profile_id,
                self._profile_institution_code,
                startTimeFormattet,
                endTimeFormattet,
            )
            # self.logger.warning("!! 2023-04-25: MIDLERTIDIGT DEAKTIVERET SØGNING I INSTITUTIONS KALENDER EFTER OPDATERING AF AULA API V16 !!")

            # Gets own events
            self.logger.info("      I personlig kalender")
            events = events + self.getEventsByProfileIdsAndResourceIds(
                self._profile_id, startTimeFormattet, endTimeFormattet
            )

            # Seems to be good with a simple cooldown time here.
            time.sleep(0.1)

        class AppointmentItem:
            pass

        aula_events = {}
        self.logger.info("Læser følgende AULA begivenhed:")

        # Fetch all event details concurrently — each getEventById is an independent GET request
        event_responses = {}
        total_events = len(events)
        completed_count = 0
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_id = {
                executor.submit(self.getEventById, event["id"]): event["id"]
                for event in events
            }
            for future in as_completed(future_to_id):
                event_responses[future_to_id[future]] = future.result()
                completed_count += 1
                if progress_callback:
                    progress_callback(completed_count, total_events)

        index = 1
        for event in events:
            response = event_responses[event["id"]]

            if not response or not response.get("data"):
                self.logger.warning(
                    "Springer begivenhed over grundet fejl! AULA returnerede ingen data "
                    "(event id: %s, svar: %s)" % (event["id"], response)
                )
                index = index + 1
                continue

            self.logger.info(
                "     (%s/%s) Begivenhed %s med startdato %s"
                % (
                    str(index),
                    str(len(events)),
                    response["data"]["title"],
                    response["data"]["startDateTime"],
                )
            )

            mAppointmentitem = AppointmentItem()
            mAppointmentitem.subject = response["data"]["title"]
            mAppointmentitem.body = response["data"]["description"]["html"]
            mAppointmentitem.aula_id = response["data"]["id"]
            mAppointmentitem.start = response["data"]["startDateTime"]
            mAppointmentitem.end = response["data"]["endDateTime"]
            mAppointmentitem.location = response["data"]["primaryResourceText"]

            description = response["data"]["description"]["html"]

            # TODO: Bruges ikke PT -  Brug AulaEvent i stedet for anden klasse.
            aula_event = AulaEvent()
            aula_event.title = response["data"]["title"]
            aula_event.description = response["data"]["description"]["html"]
            aula_event.id = response["data"]["id"]
            aula_event.start_date_time = response["data"]["startDateTime"]
            aula_event.end_date_time = response["data"]["endDateTime"]
            aula_event.location = response["data"]["primaryResourceText"]

            m1 = re.search(r"o2a_outlook_GlobalAppointmentID=\S*", description)
            if m1:
                outlook_GlobalAppointmentID = m1.group(0)
                outlook_GlobalAppointmentID = outlook_GlobalAppointmentID.split("=")[
                    1
                ].strip()
                outlook_GlobalAppointmentID = self.__remove_html_tags(
                    outlook_GlobalAppointmentID
                ).strip()

            # FINDS LMT in description
            m2 = re.search(
                r"o2a_outlook_LastModificationTime=\S* \S*\S\S:\S\S", description
            )
            if m2:
                outlook_LastModificationTime = m2.group(0)
                outlook_LastModificationTime = outlook_LastModificationTime.split("=")[
                    1
                ].strip()
                outlook_LastModificationTime = self.__remove_html_tags(
                    outlook_LastModificationTime
                ).strip()

            # Hvis måde opdateringsdatoen og ID fundet
            if m1 and m2:
                isDuplicate = False
                if outlook_GlobalAppointmentID in aula_events:
                    pass

                aula_events[outlook_GlobalAppointmentID] = {
                    "appointmentitem": mAppointmentitem,
                    "isDuplicate": isDuplicate,
                    "outlook_GlobalAppointmentID": outlook_GlobalAppointmentID,
                    "outlook_LastModificationTime": outlook_LastModificationTime,
                }
            # Hvis kun GlobalID er fundet, da skal begivenheden opdateres. Derfor omsættes LastModificationTime til 2 år før d.d. Da det vil beføre en opdatering.
            elif m1 and m2 is None:
                isDuplicate = False
                if outlook_GlobalAppointmentID in aula_events:
                    pass

                aula_events[outlook_GlobalAppointmentID] = {
                    "appointmentitem": mAppointmentitem,
                    "isDuplicate": isDuplicate,
                    "outlook_GlobalAppointmentID": outlook_GlobalAppointmentID,
                    "outlook_LastModificationTime": datetime.datetime.now()
                    + relativedelta(years=-2),
                }

            index = index + 1

        # self.signals.reading_status.emit("Afsluttet")
        return aula_events

    def getEventsForInstitutions(
        self, profileId, instCodes, startDateTime, endDateTime
    ):
        session = self._session
        url = self._aula_api_url

        params = {
            "method": "calendar.getEventsForInstitutions",
        }

        events = []

        data = {"instCodes": [instCodes], "start": startDateTime, "end": endDateTime}

        response = session.post(url, params=params, json=data).json()
        try:
            for event in response["data"]:
                if (
                    event["type"] == "event"
                    and profileId == event["creatorInstProfileId"]
                ):
                    events.append(event)
        except TypeError as e:
            self.logger.critical(
                "getEventsForInstitutions fejlede. Fuldt svar fra AULA:"
            )
            self.logger.critical(json.dumps(response, indent=4))
            self.logger.critical(e)

        return events

    def getEventsByProfileIdsAndResourceIds(
        self, profileId, startDateTime, endDateTime
    ):
        session = self._session
        url = self._aula_api_url

        params = {
            "method": "calendar.getEventsByProfileIdsAndResourceIds",
        }

        events = []
        # FORMAT:"2021-05-17 08:00:00.0000+02:00"
        data = {
            "instProfileIds": [profileId],
            "resourceIds": [],
            "start": startDateTime,
            "end": endDateTime,
        }

        response = session.post(url, params=params, json=data).json()
        # response = session.get(url).json()
        # print(json.dumps(response, indent=4))

        try:
            for event in response["data"]:
                if (
                    event["type"] == "event"
                    and profileId == event["creatorInstProfileId"]
                ):
                    events.append(event)
        except TypeError as e:
            self.logger.critical("Der skete en fejl:")
            self.logger.critical(e)

        return events

    def getEventById(self, event_id):
        session = self._session
        url = self._aula_api_url

        params = {
            "method": "calendar.getEventById",
            "eventId": event_id,
        }

        response = session.get(url, params=params).json()
        return response
