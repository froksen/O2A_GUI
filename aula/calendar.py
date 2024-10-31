# This Python file uses the following encoding: utf-8
from aula.aula_event import AulaEvent
import datetime

class Calendar:
    def __init__(self, session, aula_api_url):
        self._aula_api_url =  aula_api_url
        self._session = session
        

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

        aula_event.description = self.teams_url_fixer(aula_event.description)

        data = {
            "creator":{"id":self.getProfileId()},
            "institutionCode":self.getProfileinstitutionCode(),
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

        description = self.teams_url_fixer(aula_event.description)

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
            'institutionCode': self.getProfileinstitutionCode(),
            'creatorInstProfileId': self.getProfileId(),
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