# This Python file uses the following encoding: utf-8
from aula.aula_event import AulaEvent
import datetime
from dateutil.relativedelta import relativedelta
import logging
from . import aula_common
from .aula_connection import AulaConnection
import time
import re
import itertools


class AulaCalendar:
    #def __init__(self, session, profile_id, profile_institution_code, aula_api_url):teams_url_fixer
    def __init__(self, aula_connection: AulaConnection):
        self._aula_api_url = aula_connection.getAulaApiUrl()
        self._session = aula_connection.getSession()
        self._profile_id = aula_connection.getProfileId()
        self._profile_institution_code = aula_connection.ProfileinstitutionCode

        #Sets logger
        self.logger = logging.getLogger('O2A')

    def __remove_html_tags(self,text):
        """Remove html tags from a string"""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

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

        aula_event.id = ""      
        aula_event.outlook_global_appointment_id =  outlookobject["outlook_GlobalAppointmentID_internal"] #outlookobject["appointmentitem"].GlobalAppointmentID #outlookobject["outlook_GlobalAppointmentID_internal"]
        aula_event.outlook_organizer = outlookobject["appointmentitem"].Organizer
        aula_event.institution_code = ""
        aula_event.creator_inst_profile_id = ""
        aula_event.title = outlookobject["appointmentitem"].subject
        aula_event.type = "event"
        aula_event.outlook_body = outlookobject["appointmentitem"].body
        aula_event.location = outlookobject["appointmentitem"].location 
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
        aula_event.outlook_required_attendees = outlookobject["appointmentitem"].RequiredAttendees.split(";")
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


    def findRecipient(self,recipient_name):
        
        
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
        
        response  = self._session.get(url, params=params).json()
        #response = session.get(url).json()
        #print(json.dumps(response, indent=4))
        recipient_profileid = -1
        try:
            for result in response["data"]["results"]:
                if result["portalRole"] == "employee":
                    recipient_profileid = result["docId"] #Appearenly its docId and not profileId

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

            response  = session.post(url, params=params, json=data).json()
            #print(json.dumps(response, indent=4))

            if(response["status"]["message"] == "OK"):
                self.logger.info("Begivenheden blev fjernet!")
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

        print("DESC")
        print(aula_event.description)
        aula_event.description = self.teams_url_fixer(f"{aula_event.description}")

        data = {
            "creator":{"id":self._profile_id()},
            "institutionCode":self._profile_institution_code(),
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
            "responseRequired": True, #aula_event.response_required, #TODO: Gøre dette på en bedre måde. Lige nu gennemtvunget at der skal spørges efter svar på AULA uanset indstilling i Outlook
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

        response_calendar = session.post(url, params=params, json=data).json()
        #print(json.dumps(response_calendar, indent=4))

        if(response_calendar["status"]["message"] == "OK"):
            self.logger.info("Begivenheden \"%s\" med start dato %s blev opdateret." %(aula_event.title,aula_event.start_date_time))
            return True
        else:
            self.logger.warning("Begivenheden \"%s\" med start dato %s blev IKKE opdateret" %(aula_event.title,aula_event.start_date_time))
            return False
        
    def createSimpleEvent(self, aula_event: AulaEvent):
    
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

        print(aula_event)

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

        response_calendar = session.post(url, params=params, json=data).json()
        #print(json.dumps(response_calendar, indent=4))

        if(response_calendar["status"]["message"] == "OK"):
            self.logger.info("Begivenheden \"%s\" med startdato %s blev oprettet." %(aula_event.title,aula_event.start_date_time))
            aula_event_id = response_calendar["data"]["data"]
            return aula_event_id
        else:
            self.logger.warning("Begivenheden \"%s\" med startdato %s blev IKKE oprettet." %(aula_event.title,aula_event.start_date_time))
            return None
        
    def getEvents(self, startDatetime, endDatetime,is_in_daylight):
       
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

            def get_daylight_timezone(is_in_daylight):
                if is_in_daylight:
                    return "+02:00"
                else:
                    return "+01:00"

            #outlookevents_from_aula = self.icalmanager.readAulaCalendarEvents()
            startTimeFormattet = lookUp_begin.strftime("%Y-%m-%dT%H:%M:%ST"+get_daylight_timezone(is_in_daylight))
            endTimeFormattet = lookUp_end.strftime("%Y-%m-%dT%H:%M:%ST"+get_daylight_timezone(is_in_daylight))

            step = step +1

            status_text = "Finder begivenheder (%i af %i)"%(step,monthsDiff)
            #self.signals.reading_status.emit(status_text)

            self.logger.info("  (%i af %i) Begivenheder fra %s til %s"%(step,monthsDiff, startTimeFormattet,endTimeFormattet))

            #Includes institution
            self.logger.info("      I institution kalender")
            events = events + self.getEventsForInstitutions(self._profile_id,self._profile_institution_code,startTimeFormattet,endTimeFormattet)
            #self.logger.warning("!! 2023-04-25: MIDLERTIDIGT DEAKTIVERET SØGNING I INSTITUTIONS KALENDER EFTER OPDATERING AF AULA API V16 !!")

            #Gets own events
            self.logger.info("      I personlig kalender")
            events = events + self.getEventsByProfileIdsAndResourceIds(self._profile_id, startTimeFormattet, endTimeFormattet)

            #Seems to be good with a simple cooldown time here. 
            time.sleep(0.1)

        class appointmentitem(object):
            pass

        aula_events = {}
        self.logger.info("Læser følgende AULA begivenhed:")
        index = 1
        for event in events:
            response = self.getEventById(event["id"])

            try:
                status_Text = "Læser begivenheder (%s/%s)" %(str(index),str(len(events)))
                #self.signals.reading_status.emit(status_Text)

                self.logger.info("     (%s/%s) Begivenhed %s med startdato %s" %(str(index),str(len(events)),response["data"]["title"],response["data"]["startDateTime"]))
            except TypeError as e:
                self.logger.warning("Springer over grundet fejl!: %s" %(e))

            mAppointmentitem = appointmentitem()
            mAppointmentitem.subject = response["data"]["title"]
            mAppointmentitem.body = response["data"]["description"]["html"]
            mAppointmentitem.aula_id = response["data"]["id"]
            mAppointmentitem.start = response["data"]["startDateTime"]
            mAppointmentitem.end = response["data"]["endDateTime"]
            mAppointmentitem.location = response["data"]["primaryResourceText"] 

            description = response["data"]["description"]["html"]

            m1 = re.search('o2a_outlook_GlobalAppointmentID=\S*', description)
            if m1:
                outlook_GlobalAppointmentID = m1.group(0)
                outlook_GlobalAppointmentID = outlook_GlobalAppointmentID.split("=")[1].strip()
                outlook_GlobalAppointmentID = self.__remove_html_tags(outlook_GlobalAppointmentID).strip()

            #FINDS LMT in description
            m2 = re.search('o2a_outlook_LastModificationTime=\S* \S*\S\S:\S\S', description)
            if m2:
                outlook_LastModificationTime = m2.group(0)
                outlook_LastModificationTime = outlook_LastModificationTime.split("=")[1].strip()
                outlook_LastModificationTime = self.__remove_html_tags(outlook_LastModificationTime).strip()

            #Hvis måde opdateringsdatoen og ID fundet
            if m1 and m2:
                isDuplicate = False 
                if outlook_GlobalAppointmentID in aula_events.keys():
                    pass

                aula_events[outlook_GlobalAppointmentID]={
                    "appointmentitem":mAppointmentitem,
                    "isDuplicate" : isDuplicate,
                    "outlook_GlobalAppointmentID":outlook_GlobalAppointmentID,
                    "outlook_LastModificationTime":outlook_LastModificationTime
                }
            #Hvis kun GlobalID er fundet, da skal begivenheden opdateres. Derfor omsættes LastModificationTime til 2 år før d.d. Da det vil beføre en opdatering.
            elif m1 and m2 is None:
                isDuplicate = False 
                if outlook_GlobalAppointmentID in aula_events.keys():
                    pass

                aula_events[outlook_GlobalAppointmentID]={
                    "appointmentitem":mAppointmentitem,
                    "isDuplicate" : isDuplicate,
                    "outlook_GlobalAppointmentID":outlook_GlobalAppointmentID,
                    "outlook_LastModificationTime":datetime.datetime.now()+relativedelta(years=-2)
                }

            index = index +1

        #self.signals.reading_status.emit("Afsluttet")
        return aula_events
    
    def getEventsForInstitutions(self,profileId,instCodes, startDateTime, endDateTime):
        session = self._session
        url = self._aula_api_url

        params = {
            'method': 'calendar.getEventsForInstitutions',
            "instCodes":[instCodes],
            "start":startDateTime,"end":endDateTime
            }

        events = []        
        #FORMAT:"2021-05-17 08:00:00.0000+02:00"

        url = url+"?method=calendar.getEventsForInstitutions&instCodes[]="+str(instCodes)+"&start="+startDateTime.replace("T+","%2B")+"&end="+endDateTime.replace("T+","%2B")

        response = session.get(url).json()
        #response = session.get(url).json()
        #print(json.dumps(response, indent=4))
        #print(response)
        for event in response["data"]:
            if(event["type"] == "event" and profileId == event["creatorInstProfileId"]):
                events.append(event)

        return events

    def getEventsByProfileIdsAndResourceIds(self,profileId, startDateTime, endDateTime):
        session = self._session
        url = self._aula_api_url

        params = {
            'method': 'calendar.getEventsByProfileIdsAndResourceIds',
            }

        events = []        
        #FORMAT:"2021-05-17 08:00:00.0000+02:00"
        data = {"instProfileIds":[profileId],"resourceIds":[],"start":startDateTime,"end":endDateTime}

        response = session.post(url, params=params, json=data).json()
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
    
    def getEventById(self,event_id):
        session = self._session
        url = self._aula_api_url

        params = {
            'method': 'calendar.getEventById',
            "eventId": event_id,
            }

        response  = session.get(url, params=params).json()
        #print(json.dumps(response, indent=4))
        return response
        try:
            recipient_profileid = response["data"]["results"][0]["docId"] #Appearenly its docId and not profileId
            print(recipient_profileid)

            return int(recipient_profileid)

        except:
            return None