# This Python file uses the following encoding: utf-8
from aula.aula_event import AulaEvent
import datetime
from dateutil.relativedelta import relativedelta
import logging
import common

class Calendar:
    def __init__(self, session, profile_id, profile_institution_code, aula_api_url):
        self._aula_api_url = aula_api_url
        self._session = session
        self._profile_id = profile_id
        self._profile_institution_code = profile_institution_code

        #Sets logger
        self.logger = logging.getLogger('O2A')
        

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

        aula_event.description = common.teams_url_fixer(aula_event.description)

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
        
    def createSimpleEvent(self, aula_event = AulaEvent):
    
        session = self._session
        
        #print("START: %s" %(startDateTime))
        #print("END: %s" %(endDateTime))
        #return

        # All API requests go to the below url
        # Each request has a number of parameters, of which method is always included
        # Data is returned in JSON
        url = self.getAulaApiUrl()
        
        ### First example API request ###
        params = {
            'method': 'calendar.createSimpleEvent'
        }

        description = common.teams_url_fixer(aula_event.description)

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
            'institutionCode': self._profile_institution_code(),
            'creatorInstProfileId': self._profile_id(),
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
            self.signals.reading_status.emit(status_text)

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
                self.signals.reading_status.emit(status_Text)

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

        self.signals.reading_status.emit("Afsluttet")
        return aula_events
    
    def getEventsForInstitutions(self,profileId,instCodes, startDateTime, endDateTime):
        session = self._session()
        url = self._aula_api_url()

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
        session = self._session()
        url = self._aula_api_url()

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