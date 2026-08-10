# This Python file uses the following encoding: utf-8
from aula.aula_event import AulaEvent
import datetime
from dateutil.relativedelta import relativedelta
import logging
from . import aula_common
from .aula_connection import AulaConnection
from .aula_event_cache import AulaEventCache
import time
import re
import random
import itertools
from peoplecsvmanager import PeopleCsvManager
import requests
import json
from .timezone_utils import format_aula_datetime

class AulaCalendar:
    # Timeout (sekunder) på hvert enkelt HTTP-kald mod Aula. Uden en timeout
    # kan et enkelt hængende kald blokere hele synkroniseringen på ubestemt
    # tid; med en timeout fejler kun den ene begivenhed, og resten fortsætter.
    _HTTP_TIMEOUT_S = 10

    # getEventById kaldes for hver begivenhed under hentning af AULA-
    # kalenderen (se getEvents). For mange/for hurtige kald rammer Aulas
    # rate-limit (bekræftet: HTTP 429/status-kode 10 under test — og
    # bekræftet i produktion: begivenheder med et helt stabilt, identisk
    # vandmærke i alle kopier blev alligevel genoprettet igen og igen på
    # tværs af flere separate, fuldt gennemførte synk-kørsler samme dag).
    # Et første forsøg med flere samtidige tråde gjorde det værre, ikke
    # bedre — flere tråde der uafhængigt retryer mod samme udtømte rate-
    # limit rammer bare muren sammen, gang på gang. Derfor: kaldene køres nu
    # helt sekventielt (ingen samtidighed), med en lille, jitret pause før
    # HVERT kald (også første forsøg), og flere forsøg med længere pause ved
    # fejl. Sammen med AulaEventCache (kun genhenter det der reelt er nyt
    # siden sidst) er dette valgt for forudsigelighed og pålidelighed frem
    # for rå hastighed.
    _EVENT_FETCH_MAX_RETRIES      = 3
    _EVENT_FETCH_RETRY_DELAY_S    = 3
    # Grundpausen (uændret) — den "hvilende" hastighed når Aula ikke viser
    # tegn på pres. Se _adaptive_pace_multiplier for hvordan den skalerer op
    # ved rate-limit-pres og ned igen ved vedvarende succes.
    _EVENT_FETCH_PACE_MIN_S       = 0.2
    _EVENT_FETCH_PACE_MAX_S       = 0.4

    # Adaptiv pause: hver gang et kald fejler (typisk rate-limit), ganges
    # grundpausen op med _ADAPTIVE_PACE_STEP_UP (op til loftet). Hver gang
    # der er set _ADAPTIVE_PACE_DECAY_STREAK rene, ukomplicerede succeser i
    # træk mens pausen er forhøjet, ganges den ned igen med
    # _ADAPTIVE_PACE_STEP_DOWN, mod grundniveauet (aldrig under 1×). Det
    # betyder vi reagerer direkte på det Aula rent faktisk siger lige nu, i
    # stedet for at gætte et fast tal der enten er for aggressivt eller
    # unødigt langsomt hele tiden.
    _ADAPTIVE_PACE_STEP_UP        = 1.5
    _ADAPTIVE_PACE_STEP_DOWN      = 0.85
    _ADAPTIVE_PACE_MAX_MULTIPLIER = 6.0
    _ADAPTIVE_PACE_DECAY_STREAK   = 15

    #def __init__(self, session, profile_id, profile_institution_code, aula_api_url):teams_url_fixer
    def __init__(self, aula_connection: AulaConnection):
        self._aula_api_url = aula_connection.getAulaApiUrl()
        self._session = aula_connection.getSession()
        self._profile_id = aula_connection.getProfileId()
        self._profile_institution_code = aula_connection.ProfileinstitutionCode

        #Sets logger
        self.logger = logging.getLogger('O2A')

        # Cache for recipient IDs so the same person isn't looked up more than once
        self._recipient_cache = {}

        # Adaptiv pause-tilstand for getEventById — se konstanterne ovenfor.
        self._adaptive_pace_multiplier = 1.0
        self._adaptive_pace_streak = 0

    def __remove_html_tags(self,text):
        """Remove html tags from a string"""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

    def _parse_o2a_watermark(self, description):
        """Udtrækker O2A's vandmærke (Outlook GlobalAppointmentID +
        LastModificationTime) fra en Aula-begivenheds HTML-beskrivelse.
        Returnerer (global_id, lmt) — begge None hvis intet vandmærke findes.
        Delt mellem getEvents() og cleanup_duplicate_events.py, så de to
        altid er enige om hvad der identificerer "samme" begivenhed."""
        global_id = None
        lmt = None

        m1 = re.search('o2a_outlook_GlobalAppointmentID=\S*', description)
        if m1:
            global_id = m1.group(0).split("=")[1].strip()
            global_id = self.__remove_html_tags(global_id).strip()

        m2 = re.search('o2a_outlook_LastModificationTime=\S* \S*\S\S:\S\S', description)
        if m2:
            lmt = m2.group(0).split("=")[1].strip()
            lmt = self.__remove_html_tags(lmt).strip()

        return global_id, lmt

    def teams_url_fixer(self,text):
        #Patterns for all the different parts of the Teams Meeting
        pattern_teams_meeting="Klik her for at deltage i mødet <https:\/\/teams.microsoft.com\/l\/meetup-join/.*" 
        pattern_know_more = "Få mere at vide <https:\/\/aka.ms\/JoinTeamsMeeting"
        pattern_meeting_options = "Mødeindstillinger <https:\/\/teams.microsoft.com\/meetingOptions.*"
        url_pattern = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

        #Looks for all the parts
        teams_meeting = re.search(pattern_teams_meeting,text)
        know_more = re.search(pattern_know_more,text)
        meeting_options = re.search(pattern_meeting_options,text)

        if teams_meeting and know_more and meeting_options:
            print("Microsoft Teams meeting fundet. Fikser urls.")

        #If they are found, then do differnt things. 
        if teams_meeting:
            url = re.search(url_pattern,teams_meeting.group(0)).group(0).replace(">","")
            text = re.sub(pattern_teams_meeting,'<p><a href=\"%s" target=\"_blank\" rel=\"noopener\">%s</a></p>'%(url,"Klik her for at deltage i mødet"),text)

        if know_more:
            url = re.search(url_pattern,know_more.group(0)).group(0).replace(">","")
            text = re.sub(pattern_know_more,'<a href=\"%s" target=\"_blank\" rel=\"noopener\">%s</a>'%(url,"Få mere at vide"),text)

        if meeting_options:
            url = re.search(url_pattern,meeting_options.group(0)).group(0).replace(">","")
            text = re.sub(pattern_meeting_options,'<a href=\"%s" target=\"_blank\" rel=\"noopener\">%s</a>'%(url,"Mødeindstillinger"),text)

        return text

    def url_fixer(self,text):
        pattern_teams = "https:\/\/teams.microsoft.com\/l\/meetup-join"
        found = re.search(pattern_teams,text)

        if found:
            text = re.sub("<","",text)
            text = re.sub(">","",text)

        #print(text)

        # return
        #return text
        pattern = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

        urls_found = re.findall(pattern, text)

        #print(urls_found)
        if urls_found:
            for url in urls_found:
                #print("URL")
                #print(url)
                #print ("/URL")

                text = re.sub(re.escape(url),'<a href=\"%s" target=\"_blank\" rel=\"noopener\">%s</a>'%(url,url),text)
        return text
            #foundText = m1.group(0)

    def convert_outlook_appointmentitem_to_aula_event(self,outlookobject) -> AulaEvent:

        #Read more about patterns: https://docs.microsoft.com/en-us/dotnet/api/microsoft.office.interop.outlook.olrecurrencetype?view=outlook-pia
        def outlook_pattern_to_aula_pattern(x):
            x = int(x)
            return {
                0: "daily",
                1: "weekly",
                2: "monthly"
            }.get(x, "never")


        aula_event = AulaEvent()

        # "Optaget"-placeholder (aula_busy_fallback): kun titlen må afsløre at tiden er optaget —
        # beskrivelse, lokation og deltagere skjules så begivenhedens indhold ikke lækkes.
        is_busy_placeholder = bool(outlookobject.get("aula_title_override"))

        aula_event.id = ""
        aula_event.outlook_global_appointment_id =  outlookobject["outlook_GlobalAppointmentID_internal"] #outlookobject["appointmentitem"].GlobalAppointmentID #outlookobject["outlook_GlobalAppointmentID_internal"]
        aula_event.outlook_organizer = outlookobject["appointmentitem"].Organizer
        aula_event.institution_code = ""
        aula_event.creator_inst_profile_id = ""
        aula_event.title = outlookobject.get("aula_title_override") or outlookobject["appointmentitem"].subject
        aula_event.type = "event"
        aula_event.outlook_body = "" if is_busy_placeholder else outlookobject["appointmentitem"].body
        aula_event.location = "" if is_busy_placeholder else outlookobject["appointmentitem"].location
        aula_event.start_date = outlookobject["aula_startdate"]
        aula_event.end_date = outlookobject["aula_enddate"]
        aula_event.start_time = outlookobject["aula_starttime"]
        aula_event.end_time = outlookobject["aula_endtime"]
        aula_event.start_timezone  = outlookobject["aula_startdate_timezone"]
        aula_event.end_timezone = outlookobject["aula_enddate_timezone"]
        aula_event.outlook_last_modification_time = outlookobject["appointmentitem"].LastModificationTime
        aula_event.all_day = outlookobject["appointmentitem"].AllDayEvent
        aula_event.private = True if outlookobject["appointmentitem"].Sensitivity == 2 else False #Værdien 2 betyder privat
        aula_event.is_recurring = outlookobject["appointmentitem"].IsRecurring
        aula_event.hide_in_own_calendar = outlookobject["hideInOwnCalendar"]
        aula_event.add_to_institution_calendar = outlookobject["addToInstitutionCalendar"]
        aula_event.is_private = True if outlookobject["appointmentitem"].Sensitivity == 2 else False #Værdien 2 betyder privat
        aula_event.outlook_required_attendees = [] if is_busy_placeholder else outlookobject["appointmentitem"].RequiredAttendees.split(";")
        aula_event.interval = outlookobject["appointmentitem"].GetRecurrencePattern().Interval
        aula_event.recurrence_pattern = outlookobject["appointmentitem"].GetRecurrencePattern()
        aula_event.max_date = str(outlookobject["appointmentitem"].GetRecurrencePattern().PatternEndDate).split(" ")[0] #Only the date part is needed. EX: 2022-02-11 00:00:00+00:00 --> 2022-02-11
        aula_event.aula_recurrence_pattern = outlook_pattern_to_aula_pattern(outlookobject["appointmentitem"].GetRecurrencePattern().RecurrenceType)
        aula_event.day_of_week_mask_list = self.get_day_of_the_week_mask(outlookobject["appointmentitem"].GetRecurrencePattern().DayOfWeekMask)
        aula_event.response_required = outlookobject["appointmentitem"].ResponseRequested

        return aula_event

    def calulate_day_of_the_week_mask(self):
        olFriday = 32    # Friday
        olMonday = 2     # Monday
        olSaturday = 64  # Saturday
        olSunday = 1     # Sunday
        olThursday = 16  # Thursday
        olTuesday = 4    # Tuesday
        olWednesday = 8  # Wednesday

        days_list = [olMonday, olTuesday, olWednesday, olThursday,
                        olFriday, olSaturday, olSunday]

        data = []
        #Used to convert from value to string
        def day_of_week_convert(x):
                            x = int(x)
                            return {
                                olSunday: "sunday",
                                olMonday: "monday",
                                olTuesday: "tuesday",
                                olWednesday: "wednesday",
                                olThursday: "thursday",
                                olFriday: "friday",
                                olSaturday: "saturday",
                            }.get(x, "unknown")

        #Find all combinations of the days_list, and creates a data dict
        for L in range(0, len(days_list)+1):
            for subset in itertools.combinations(days_list, L):
                sum = 0
                days_text = []
                for i in subset:
                    sum = sum + i
                    days_text.append(day_of_week_convert(i))

                days_info = {
                    "days_integer": subset,
                    "days_string": days_text,
                    "sum": sum
                }     

                data.append(days_info)

        return data

    def get_day_of_the_week_mask(self,sum):
        days_combinations = self.calulate_day_of_the_week_mask()

        for day in days_combinations:
            if sum == day["sum"]:
                return day["days_integer"]

        return False
    
    def find_recipient_alias(self,recipient_name)->str:
        peoplecsvmanager = PeopleCsvManager()

        csv_aula_name = peoplecsvmanager.getPersonData(recipient_name)

        self.logger.debug(f"      Undersøger om personen {recipient_name} har et ALIAS")
        self.logger.debug(csv_aula_name)
        if not csv_aula_name == None:
            self.logger.info("      OBS: Deltagerens %s Outlook navn blev fundet i CSV-filen og blev erstattet med %s" %(recipient_name,csv_aula_name))
            return csv_aula_name
        
        return recipient_name
    
    def should_ignore_recipient(self, recipient_name) -> bool:
        csv_aula_name = PeopleCsvManager().getPersonData(recipient_name)
        if csv_aula_name == "IGNORE_PERSON":
            self.logger.info("      OBS: Deltagerens %s Outlook navn blev fundet i IGNORER-filen og vil derfor ikke blive tilføjet til begivenheden" %(recipient_name))
            return True
        
        return False

    
    def handle_recipients(self, event):
        #If event has been created by some one else. Set in description that its the case.
        #if not str(self.outlookmanager.get_personal_calendar_username()).strip() == str(event.outlook_organizer).strip(): 
        #    self.logger.debug("Begivenheden er blevet oprettet af en anden person. Tilføjer dette til beskrivelsen.")
        #    event.outlook_body = "<p><b>OBS:</b> Begivenheden er oprindelig oprettet af: %s" %(str(event.outlook_organizer).strip()) + "</p>" +  event.outlook_body
        #    return event
        

        self.logger.info("Søger efter deltagere:")
        for attendee in event.outlook_required_attendees:
            attendee = attendee.strip() #Fjerner potentielle whitespaces foran og bagved navn
            attendee = attendee.split("(")[0].strip() #Fjerner potentielle mailadresser i navne

            if attendee == str(event.outlook_organizer) or attendee == "":
                self.logger.debug("     Deltageren er arrangør - Springer over")
                continue
            

            #Checks if person should be replaced with other name from CSV-file
            csv_aula_name = self.peoplecsvmanager.getPersonData(attendee)

            if csv_aula_name == "IGNORE_PERSON":
                self.logger.info("      OBS: Deltagerens %s Outlook navn blev fundet i IGNORER-filen og vil derfor ikke blive tilføjet til begivenheden" %(attendee))
                continue

            if not csv_aula_name == None:
                self.logger.info("      OBS: Dektagerens %s Outlook navn blev fundet i CSV-filen og blev erstattet med %s" %(attendee,csv_aula_name))
                attendee = csv_aula_name

            #Searching for name in AULA
            self.logger.info("      OBS: Deltageren %s Outlook navn slås op direkte på AULA." %(attendee))
            search_result = self.aulamanager.findRecipient(attendee)

            if not search_result == None:
                self.logger.info("      Deltager %s blev fundet i AULA!" %(attendee))
                event.attendee_ids.append(search_result)
            else:
                self.logger.info("      Deltager %s blev IKKE fundet i AULA ved første af to forsøg" %(attendee))
                
                time.sleep(2)

                search_result = AulaCalendar.findRecipient(attendee)
                if not search_result == None:
                    self.logger.info("      Deltager %s blev fundet i AULA ved 2. forsøg!" %(attendee))
                    event.attendee_ids.append(search_result)
                else:
                    self.logger.info("      Deltager %s blev IKKE fundet i AULA ved anden af to forsøg." %(attendee))
                    event.creation_or_update_errors.attendees_not_found.append(attendee)
            time.sleep(0.5)

        return event

    def get_atendees_ids(self,event: AulaEvent):
        for attendee in event.outlook_required_attendees:
            attendee = str(attendee).strip()
            attendee = attendee.split("(")[0].strip() #Fjerner potentielle mailadresser i navne

            self.logger.info(f"     Søger efter deltageren \"%s\" på AULA." %(attendee))

            if attendee == str(event.outlook_organizer) or attendee == "":
                self.logger.info("     Deltageren er arrangør - Springer over")
                continue

            #Finder eventuelt alias som personen har
            attendee = self.find_recipient_alias(attendee)

            #Om personen skal ignoreres eller ej.
            if self.should_ignore_recipient(attendee) == True or attendee == "IGNORE_PERSON":
                self.logger.info("     OBS: Deltagerens blev fundet i IGNORER-filen - Springer over")
                continue

            #Slår personen op på AULA, og får ID´et herfra.
            search_for_recipient_attempts = 1
            search_for_recipient_attempts_max = 2

            attendee_found = False
            while search_for_recipient_attempts <= search_for_recipient_attempts_max and not attendee_found == True:
                search_result = "Blev ikke fundet."
                attendee_id = self.findRecipient(attendee)
                if not attendee_id is None:
                    event.attendee_ids.append(attendee_id)
                    attendee_found = True
                    search_result = "Blev fundet. Undlader at prøve igen."
                    self.logger.info(f"       (Forsøg {search_for_recipient_attempts} af {search_for_recipient_attempts_max} : {search_result}")
                    break  # Found — no need to sleep or retry

                self.logger.info(f"       (Forsøg {search_for_recipient_attempts} af {search_for_recipient_attempts_max} : {search_result}")

                if search_for_recipient_attempts == 2 and attendee_id is None:
                    event.creation_or_update_errors.attendees_not_found.append(attendee)

                search_for_recipient_attempts = search_for_recipient_attempts + 1
                time.sleep(1)  # Only sleep before a retry, not after a successful find



        return event

    def findRecipient(self,recipient_name):

        if recipient_name in self._recipient_cache:
            self.logger.info(f"     Deltager \"{recipient_name}\" fundet i cache.")
            return self._recipient_cache[recipient_name]

        params = {
            'method': 'search.findRecipients',
            "text": recipient_name,
            "query": recipient_name,
            "id": str(self._profile_id),
            "typeahead": "true",
            "limit": "100",
            "scopeEmployeesToInstitution" : "true",
            "instCode": str(self._profile_institution_code),
            "fromModule":"event",
            "docTypes[]":"Profile",
            "docTypes[]":"Group"
            }

        #url = " https://www.aula.dk/api/v11/?method=search.findRecipients&text=Stefan&query=Stefan&id=779467&typeahead=true&limit=100&scopeEmployeesToInstitution=false&fromModule=event&instCode=537007&docTypes[]=Profile&docTypes[]=Group"
        url = self._aula_api_url+"?method=search.findRecipients&text="+recipient_name+"&query="+recipient_name+"&id="+str(self._profile_id)+"&typeahead=true&limit=100&scopeEmployeesToInstitution=true&fromModule=event&instCode="+str(self._profile_institution_code)+"&docTypes[]=Profile&docTypes[]=Group"
        
        response  = self._session.get(url, params=params, timeout=self._HTTP_TIMEOUT_S).json()
        #response = session.get(url).json()
        #print(json.dumps(response, indent=4))
        recipient_profileid = -1
        try:
            for result in response["data"]["results"]:
                if result["portalRole"] == "employee":
                    recipient_profileid = result["docId"] #Appearenly its docId and not profileId
                    self._recipient_cache[recipient_name] = int(recipient_profileid)
                    return int(recipient_profileid)


        except:
            return None


    def deleteEvent(self, eventId):
            session = self._session
            url = self._aula_api_url

            params = {
                'method': 'calendar.deleteEvent'
                }

            data = {
                "id":eventId
            }

            response  = session.post(url, params=params, json=data, timeout=self._HTTP_TIMEOUT_S).json()
            #print(json.dumps(response, indent=4))

            if(response["status"]["message"] == "OK"):
                #self.logger.info("Begivenheden blev fjernet!")
                return True
            else:
                self.logger.warning("Begivenheden blev IKKE fjernet!")
                return False


    def updateEvent(self, aula_event):
        session = self._session
        url = self._aula_api_url

        params = {
            'method': 'calendar.updateSimpleEvent'
            }

        aula_event.description = self.teams_url_fixer(f"{aula_event.description}")

        data = {
            "creator":{"id":self._profile_id},
            "institutionCode":self._profile_institution_code,
            "description":aula_event.description,
            'primaryResource': {},
            'additionalResourceText' : aula_event.location,
            "additionalResources":[],
            "invitees":[],
            "invitedGroups":[],
            "attachments":[],
            "pendingMedia":False,
            "timeSlot":None,
            "vacationRegistration":None,
            "isDeleted":False,
            "eventClass":"basic",
            "responseDeadline":None,
            "isDeadlineExceeded":False,
            'addToInstitutionCalendar': aula_event.add_to_institution_calendar,
            'hideInOwnCalendar': aula_event.hide_in_own_calendar,
            "invitedGroupHomeChildren":[],
            "id":aula_event.id,
            "title":aula_event.title,
            "allDay":aula_event.all_day,
            "startDateTime": aula_event.start_date_time , #"2021-10-03T10:10:00.0000+02:00",
            "endDateTime":aula_event.end_date_time, #"2021-10-03T12:00:00.0000+02:00",
            #"oldEndDateTime":"2021-10-03T10:00:00+00:00",
            #"oldStartDateTime":"2021-10-03T01:10:00+00:00",
            "responseRequired": aula_event.response_required, 
            "private":aula_event.is_private,
            "type":"event",
            "addedToInstitutionCalendar":False,
            #"start":"2021-10-03T01:10:00+00:00",
            #"end":"2021-10-03T10:00:00+00:00",
            "invitedGroupHomes":[],
            "additionalLocations":[],
            "resources":[],
            "pattern":"never",
            "occurenceLimit":0,
            "weekdayMask":[False,False,False,False,False,False,False],
            "maxDate":None,
            "interval":0,
            "eventId":aula_event.id,
            "isPrivate":aula_event.is_private,
            "inviteeIds": aula_event.attendee_ids, #[],
            "invitedGroupIds":[],
            "resourceIds":[],
            "additionalLocationIds":[],
            "additionalResourceIds":[],
            "attachmentIds":[],
            "isEditEvent":True
            }

        response_calendar = session.post(url, params=params, json=data, timeout=self._HTTP_TIMEOUT_S).json()
        #print(json.dumps(response_calendar, indent=4))

        try:
            if(response_calendar["status"]["message"] == "OK"):
                self.logger.info("Begivenheden \"%s\" med start dato %s blev opdateret." %(aula_event.title,aula_event.start_date_time))
                return True
            else:
                self.logger.warning("Begivenheden \"%s\" med start dato %s blev IKKE opdateret" %(aula_event.title,aula_event.start_date_time))
                return False
        except requests.exceptions.Timeout as errt:
            self.logger.info(f"(TIMEOUT) Begivenheden blev ikke opdateret, grundet manglende svar fra AULA")
            self.logger.debug(errt)
            return None
        
    def createSimpleEvent(self, aula_event: AulaEvent) -> str|str:

        session = self._session
        
        #print("START: %s" %(startDateTime))
        #print("END: %s" %(endDateTime))
        #return

        # All API requests go to the below url
        # Each request has a number of parameters, of which method is always included
        # Data is returned in JSON
        url = self._aula_api_url
        
        ### First example API request ###
        params = {
            'method': 'calendar.createSimpleEvent'
        }

        description = self.teams_url_fixer(f"{aula_event.description}")

        data = {
            'title': aula_event.title,
            'description': description,
            'startDateTime': aula_event.start_date_time, # 2021-05-18T14:30:00.0000+02:00
            'endDateTime': aula_event.end_date_time, # '2021-05-18T15:00:00.0000+02:00'
            'startDate': datetime.datetime.today().strftime('%Y-%m-%d'), #Is always today
            'endDate': datetime.datetime.today().strftime('%Y-%m-%d'), # is always today
            #'startTime': '12:00:19', 
            #'endTime': '12:30:19',
            'id': '',
            'institutionCode': self._profile_institution_code,
            'creatorInstProfileId': self._profile_id,
            'type': 'event',
            'allDay': aula_event.all_day,
            'private': aula_event.is_private,
            'primaryResource': {},
            'additionalResourceText' : aula_event.location,
            'additionalLocations': [],
            'invitees': [],
            'invitedGroups': [],
            'invitedGroupIds': [],
            'invitedGroupHomes': [],
            "responseRequired": True, #aula_event.response_required, #TODO: Gøre dette på en bedre måde. Lige nu gennemtvunget at der skal spørges efter svar på AULA uanset indstilling i Outlook
            'responseDeadline': None,
            'resources': [],
            'attachments': [],
            'oldStartDateTime': '',
            'oldEndDateTime': '',
            'isEditEvent': False,
            'addToInstitutionCalendar': aula_event.add_to_institution_calendar,
            'hideInOwnCalendar': aula_event.hide_in_own_calendar,
            'inviteeIds': aula_event.attendee_ids,
            'additionalResources': [],
            'pattern': 'never',
            'occurenceLimit': 0,
            'weekdayMask': [
                False,
                False,
                False,
                False,
                False,
                False,
                False
            ],
            'maxDate': None,
            'interval': 0,
            'lessonId': '',
            'noteToClass': '',
            'noteToSubstitute': '',
            'eventId': '',
            'isPrivate': aula_event.is_private,
            'resourceIds': [],
            'additionalLocationIds': [],
            'additionalResourceIds': [],
            'attachmentIds': []
        }


        try:
            response_calendar = session.post(url, params=params, json=data, timeout=self._HTTP_TIMEOUT_S).json()
            #print(json.dumps(response_calendar, indent=4))

            if(response_calendar["status"]["message"] == "OK"):
            #    self.logger.info("Begivenheden \"%s\" med startdato %s blev oprettet." %(aula_event.title,aula_event.start_date_time))
                aula_event_id = response_calendar["data"]["data"]
                return aula_event_id,"SUCCESS"
            else:
            #    self.logger.warning("Begivenheden \"%s\" med startdato %s blev IKKE oprettet." %(aula_event.title,aula_event.start_date_time))
                json_response_dump = json.dumps(response_calendar, indent=4)
                return None,json_response_dump
        except requests.exceptions.Timeout as errt:
            self.logger.info(f"(TIMEOUT) Begivenheden blev ikke oprettet, grundet manglende svar fra AULA")
            self.logger.debug(errt)
            return None, errt
        
    def _format_lookup_datetime(self, local_dt):
        return format_aula_datetime(local_dt)

    def getEvents(self, startDatetime, endDatetime, progress_callback=None, force_refresh=False):
        """force_refresh=True springer den lokale detalje-cache helt over og
        henter alt friskt fra Aula — brugt af 'Tving fuld synkronisering',
        så brugeren altid har en måde at få frisk, garanteret korrekt data
        på, hvis de har mistanke om at cachen er forkert."""

        #Calculates the diffence between the dates.
        monthsDiff = abs((endDatetime.year - startDatetime.year)) * 12 + abs(endDatetime.month - startDatetime.month)

        #Makes sure that even if only one event in same month, the loop will be run
        if monthsDiff <= 0:
            monthsDiff = 1

        events = []
        self.logger.info("Læser AULA kalendere")
        self.logger.info("Lokaliserer begivenheder i kalendere")
        step = 0
        for months in range(monthsDiff):
            lookUp_begin = startDatetime + relativedelta(months=months)
            lookUp_end = startDatetime + relativedelta(months=months+1)

            #End date can not be later than end date specified.
            if lookUp_end >= endDatetime:
                lookUp_end = endDatetime

            #outlookevents_from_aula = self.icalmanager.readAulaCalendarEvents()
            startTimeFormattet = self._format_lookup_datetime(lookUp_begin)
            endTimeFormattet = self._format_lookup_datetime(lookUp_end)

            step = step +1

            status_text = "Finder begivenheder (%i af %i)"%(step,monthsDiff)
            #self.signals.reading_status.emit(status_text)

            self.logger.info("  (%i af %i) Begivenheder fra %s til %s"%(step,monthsDiff, startTimeFormattet,endTimeFormattet))

            # calendar.getEventsForInstitutions er ikke længere en gyldig Aula
            # API-metode (bekræftet: fejler altid med status-kode 40 — Aulas
            # eget frontend kalder den heller ikke længere). Institutionskalender-
            # begivenheder kommer nu med i samme svar som de personlige, markeret
            # med addedToInstitutionCalendar — der er derfor intet særskilt kald
            # tilbage at foretage her.
            self.logger.info("      I personlig kalender")
            events = events + self.getEventsByProfileIdsAndResourceIds(self._profile_id, startTimeFormattet, endTimeFormattet)

            #Seems to be good with a simple cooldown time here. 
            time.sleep(0.1)

        class appointmentitem(object):
            pass

        aula_events = {}
        total_events = len(events)
        cache_hits = 0
        cache_misses = 0
        self.logger.info(
            f"Læser detaljer for {total_events} AULA-begivenheder "
            f"(bruger lokal cache hvor muligt — se aula_event_cache.py)…")

        # Sekventielt, med forbrug — se get_event_details_cached/getEventById
        # for hvorfor (samtidige kald med retry viste sig at forværre Aulas
        # rate-limit i stedet for at afhjælpe den).
        for index, event in enumerate(events, start=1):
            entry, from_cache = self.get_event_details_cached(event["id"], bypass_cache=force_refresh)
            if from_cache:
                cache_hits += 1
            else:
                cache_misses += 1

            if entry is None:
                self.logger.warning(
                    "Springer begivenhed over grundet fejl! AULA returnerede ingen data, "
                    "eller begivenheden har intet O2A-vandmærke (event id: %s)" % event["id"])
            else:
                mAppointmentitem = appointmentitem()
                mAppointmentitem.subject = entry["title"]
                mAppointmentitem.aula_id = event["id"]
                mAppointmentitem.start = entry["start"]
                mAppointmentitem.end = entry["end"]
                mAppointmentitem.location = entry["location"]

                outlook_GlobalAppointmentID = entry["global_id"]
                # Hvis kun GlobalID blev fundet i vandmærket (ikke LMT), skal
                # begivenheden opdateres — derfor omsættes LastModificationTime
                # til 2 år før d.d., hvilket altid vil udløse en opdatering.
                outlook_LastModificationTime = entry["lmt"] or (datetime.datetime.now()+relativedelta(years=-2))

                isDuplicate = outlook_GlobalAppointmentID in aula_events
                if isDuplicate:
                    self.logger.warning(
                        "Fandt flere AULA-begivenheder med samme Outlook-nøgle "
                        "(%s) — sandsynligvis en dublet fra en tidligere fejlslagen "
                        "synk. Kør cleanup_duplicate_events.py for at rydde op." % outlook_GlobalAppointmentID)

                aula_events[outlook_GlobalAppointmentID]={
                    "appointmentitem":mAppointmentitem,
                    "isDuplicate" : isDuplicate,
                    "outlook_GlobalAppointmentID":outlook_GlobalAppointmentID,
                    "outlook_LastModificationTime":outlook_LastModificationTime
                }

            if progress_callback:
                progress_callback(index, total_events)

        self.logger.info(f"Færdig — {cache_hits} fra cache, {cache_misses} hentet friskt fra Aula.")
        removed = AulaEventCache.prune_to([event["id"] for event in events])
        if removed:
            self.logger.info(f"Ryddede {removed} forældede poster fra begivenheds-cachen (ikke længere i Aula).")

        return aula_events

    def getEventsByProfileIdsAndResourceIds(self,profileId, startDateTime, endDateTime):
        session = self._session
        url = self._aula_api_url

        params = {
            'method': 'calendar.getEventsByProfileIdsAndResourceIds',
            }

        events = []        
        #FORMAT:"2021-05-17 08:00:00.0000+02:00"
        data = {"instProfileIds":[profileId],"resourceIds":[],"start":startDateTime,"end":endDateTime}

        response = session.post(url, params=params, json=data, timeout=self._HTTP_TIMEOUT_S).json()
        #response = session.get(url).json()
        #print(json.dumps(response, indent=4))

        try:
            for event in response["data"]:
                if(event["type"] == "event" and profileId == event["creatorInstProfileId"]):
                    events.append(event)
        except TypeError as e:
            self.logger.critical("Der skete en fejl:")
            self.logger.critical(e)

        return events
    
    def get_event_details_cached(self, event_id, bypass_cache=False):
        """Returnerer (entry, from_cache) for én Aula-begivenhed. entry er en
        dict med title/start/end/location/global_id/lmt, eller None hvis
        begivenheden ikke kunne hentes eller ikke har et O2A-vandmærke (dvs.
        ikke er oprettet af O2A). from_cache angiver om svaret kom fra den
        lokale cache uden noget netværkskald.

        bypass_cache=True (brugt af 'Tving fuld synkronisering') ignorerer
        cachen og henter altid friskt — den garanterede vej til frisk,
        korrekt data hvis brugeren har mistanke om at cachen er forkert."""
        if not bypass_cache:
            cached = AulaEventCache.get(event_id)
            if cached is not None:
                return cached, True

        response = self.getEventById(event_id)
        if not response or not response.get("data"):
            return None, False

        data = response["data"]
        description = data["description"]["html"]
        global_id, lmt = self._parse_o2a_watermark(description)
        if not global_id:
            return None, False

        entry = {
            "title": data.get("title"),
            "start": data.get("startDateTime"),
            "end": data.get("endDateTime"),
            "location": data.get("primaryResourceText"),
            "created": data.get("createdDateTime"),
            "global_id": global_id,
            "lmt": lmt,
        }
        AulaEventCache.put(event_id, entry)
        return entry, False

    def _note_pace_failure(self):
        """Et kald fejlede — sandsynligvis rate-limit. Øg pausen mellem
        fremtidige kald i denne kørsel, indtil vi ser vedvarende succes igen."""
        before = self._adaptive_pace_multiplier
        self._adaptive_pace_multiplier = min(
            self._adaptive_pace_multiplier * self._ADAPTIVE_PACE_STEP_UP,
            self._ADAPTIVE_PACE_MAX_MULTIPLIER)
        self._adaptive_pace_streak = 0
        if self._adaptive_pace_multiplier > before:
            self.logger.info(
                f"Øger pausen mellem AULA-kald pga. rate-limit-pres — "
                f"nu {self._adaptive_pace_multiplier:.1f}× grundpausen.")

    def _note_pace_success(self, first_try: bool):
        """Et kald lykkedes. Kun rene, ukomplicerede succeser (første forsøg)
        tæller mod at sænke en forhøjet pause igen — en succes efter retry
        er stadig et tegn på nyligt pres."""
        if not first_try or self._adaptive_pace_multiplier <= 1.0:
            return
        self._adaptive_pace_streak += 1
        if self._adaptive_pace_streak < self._ADAPTIVE_PACE_DECAY_STREAK:
            return
        self._adaptive_pace_streak = 0
        before = self._adaptive_pace_multiplier
        self._adaptive_pace_multiplier = max(
            self._adaptive_pace_multiplier * self._ADAPTIVE_PACE_STEP_DOWN, 1.0)
        if self._adaptive_pace_multiplier < before:
            self.logger.info(
                f"Sænker pausen mellem AULA-kald igen efter vedvarende succes — "
                f"nu {self._adaptive_pace_multiplier:.1f}× grundpausen.")

    def getEventById(self,event_id):
        """Henter én begivenheds fulde detaljer via calendar.getEventById.
        Aula rate-limiter den slags (bekræftet: HTTP 429/status-kode 10), og
        et enkelt ramt kald må ikke få en begivenhed der rent faktisk findes
        til at fremstå som manglende for denne synk. Der holdes derfor en
        lille, jitret pause før HVERT forsøg (også det første) for ikke selv
        at ramme Aula for hårdt — grundpausen skaleres adaptivt op ved pres
        og ned igen ved vedvarende succes (se _note_pace_failure/_success) —
        og hvert kald forsøges igen med stigende pause før vi giver op og
        lader kaldstedet logge/springe begivenheden over. Kaldes normalt kun
        for begivenheder der IKKE allerede findes i AulaEventCache — se
        get_event_details_cached."""
        session = self._session
        url = self._aula_api_url

        params = {
            'method': 'calendar.getEventById',
            "eventId": event_id,
            }

        response = None
        for attempt in range(self._EVENT_FETCH_MAX_RETRIES):
            pace = random.uniform(self._EVENT_FETCH_PACE_MIN_S, self._EVENT_FETCH_PACE_MAX_S)
            time.sleep(pace * self._adaptive_pace_multiplier)
            try:
                response = session.get(url, params=params, timeout=self._HTTP_TIMEOUT_S).json()
            except Exception as e:
                self.logger.warning(
                    f"getEventById({event_id}) HTTP-kald fejlede (forsøg "
                    f"{attempt + 1}/{self._EVENT_FETCH_MAX_RETRIES}): {e}")
                response = None

            if response and response.get("data"):
                self._note_pace_success(first_try=(attempt == 0))
                return response

            self._note_pace_failure()
            if attempt < self._EVENT_FETCH_MAX_RETRIES - 1:
                self.logger.warning(
                    f"getEventById({event_id}) fik intet data (forsøg "
                    f"{attempt + 1}/{self._EVENT_FETCH_MAX_RETRIES}, muligvis rate-limit) "
                    f"— venter {self._EVENT_FETCH_RETRY_DELAY_S * (attempt + 1)}s før nyt forsøg.")
                time.sleep(self._EVENT_FETCH_RETRY_DELAY_S * (attempt + 1))

        return response
