from dateutil.relativedelta import relativedelta
from aulaevent import AulaEvent
from outlookmanager import OutlookManager
from aulamanager import AulaManager
import datetime as dt
import time
import logging
import sys
import win32com.client
import keyring
from setupmanager import SetupManager
from peoplecsvmanager import PeopleCsvManager
import itertools
import pytz
from databasemanager import DatabaseManager as dbManager
from PySide6.QtCore import QObject, Signal


class EventMangerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        int indicating % progress

    '''
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    outlook_status = Signal(object)
    aula_status = Signal(object)
    unilogin_status = Signal(object)
    update_status = Signal(object)

    progress = Signal(int)

class EventManager:
    def __init__(self):
        #Managers are init.
        self.aulamanager = AulaManager()
        self.outlookmanager = OutlookManager()
        self.setupmanager = SetupManager()
        self.peoplecsvmanager = PeopleCsvManager()
        self.signals = EventMangerSignals()

        self.aulamanager.signals.reading_status.connect(self.signals.aula_status)

        #Sets logger
        self.logger = logging.getLogger('O2A')

        #self.login_to_aula()
    

    def login_to_aula(self):
        #Gets AULA password and username from keyring
        aula_usr = self.setupmanager.get_aula_username()
        aula_pwd = self.setupmanager.get_aula_password()
        

        #Login to AULA
        self.signals.unilogin_status.emit("Forsøger at logge på")
        login_response = self.aulamanager.login(aula_usr,aula_pwd)
        if not login_response.status == True:
            #self.signals.status.emit("Logind mislykkedes")
            self.logger.critical("Programmet stoppede uventet, da det ikke kunne logge ind på AULA!.")
            self.outlookmanager.send_a_mail(login_response)
            sys.exit()
            return
        self.signals.unilogin_status.emit("Logind lykkedes")

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

    def _basic_aula_event_actions(self, event):

        #mdbManager = dbManager()

        #If event has been created by some one else. Set in description that its the case.
        if not str(self.outlookmanager.get_personal_calendar_username()).strip() == str(event.outlook_organizer).strip(): 
            self.logger.debug("Begivenheden er blevet oprettet af en anden person. Tilføjer dette til beskrivelsen.")
            event.outlook_body = "<p><b>OBS:</b> Begivenheden er oprindelig oprettet af: %s" %(str(event.outlook_organizer).strip()) + "</p>" +  event.outlook_body

        #Only attempt to add attendees to event if created by the user them self. 
        if str(self.outlookmanager.get_personal_calendar_username()).strip() == str(event.outlook_organizer).strip(): 

            self.logger.info("Søger efter deltagere:")
            for attendee in event.outlook_required_attendees:
                attendee = attendee.strip()

                if attendee == str(event.outlook_organizer) or attendee == "":
                    self.logger.debug("     Deltageren er arrangør - Springer over")
                    continue

                #Removes potential emails from contact name
                attendee = attendee.split("(")[0].strip()

                #Checks if person should be replaced with other name from CSV-file
                csv_aula_name = self.peoplecsvmanager.getPersonData(attendee)

                if not csv_aula_name == None and not csv_aula_name == "IGNORE_PERSON":
                    self.logger.info("      OBS: Dektagerens %s Outlook navn blev fundet i CSV-filen og blev erstattet med %s" %(attendee,csv_aula_name))
                    attendee = csv_aula_name

                #Searching for name in AULA
                if not csv_aula_name == "IGNORE_PERSON":
                    #db_search_result = mdbManager.get_recipient_id(attendee) #Prøver først i DB
                    #search_result = db_search_result

                    #if db_search_result is None: #Hvis ikke fundet noget i DB, da prøver at slå op på AULA.
                    self.logger.info("      OBS: Deltageren %s Outlook navn slås op direkte på AULA." %(attendee))

                    search_result = self.aulamanager.findRecipient(attendee)

                if csv_aula_name == "IGNORE_PERSON":
                    self.logger.info("      OBS: Deltagerens %s Outlook navn blev fundet i IGNORER-filen og vil derfor ikke blive tilføjet til begivenheden" %(attendee))
                elif not search_result == None:
                    self.logger.info("      Deltager %s blev fundet i AULA!" %(attendee))
                    #mdbManager.update_recipient_record(search_result,attendee) #Tilføjer til DB. 
                    event.attendee_ids.append(search_result)
                else:
                    self.logger.info("      Deltager %s blev IKKE fundet i AULA!" %(attendee))

                    event.creation_or_update_errors.attendees_not_found.append(attendee)
                time.sleep(0.5)

        return event


    def update_aula_calendar(self, changes):

        #If no changes, then do nothing
        if len(changes['events_to_create']) <= 0 and len(changes['events_to_remove']) <= 0 and len(changes['events_to_update']) <= 0:
            self.signals.update_status.emit("Ingen ændringer. Processen er afsluttet")
            self.logger.info("Ingen ændringer. Processen er afsluttet")
            return

        #Opretter forbindelse til DB
        #mdbManager = dbManager()

        events_with_errors = []

        for event_to_remove in changes['events_to_remove']:
            event_title = event_to_remove["appointmentitem"].subject
            event_id = event_to_remove["appointmentitem"].aula_id #Should be regexp instead!
            self.logger.info("Prøver at FJERNE begivenheden: %s " %(event_title))
            rlt = self.aulamanager.deleteEvent(event_id)

            self.signals.update_status.emit("Prøver at FJERNE begivenheden: %s " %(event_title))
            if not rlt == True:
                event_to_remove.creation_or_update_errors.event_not_deleted = True
                events_with_errors.append(event_to_remove) 

        for event_to_update in changes["events_to_update"]:
            event_to_update = self._basic_aula_event_actions(event_to_update)
            
            self.signals.update_status.emit("Opdaterer begivenheden: %s " %(event_to_update.title))

            is_Recurring = event_to_update.is_recurring #TODO: Gør via variable
            if is_Recurring:
                rlt = self.aulamanager.updateRecuringEvent(event_to_update)
            else:
                rlt = self.aulamanager.updateEvent(event_to_update)

            if not rlt == True:
                event_to_update.creation_or_update_errors.event_not_update_or_created = True

            if event_to_update.creation_or_update_errors.event_not_update_or_created == True or len(event_to_update.creation_or_update_errors.attendees_not_found)>0:
                events_with_errors.append(event_to_update)    

            #Hvis begivenheden blev opdateret korrekt, da bliver optegnelsen i SQL databasen opdateret.
            #if rlt == True:
                #mdbManager.update_event_record(event_to_update.outlook_global_appointment_id,event_to_update.id)

        #Creation of event
        for event_to_create in changes['events_to_create']:
            event_to_create = self._basic_aula_event_actions(event_to_create)

            self.signals.update_status.emit("Opdaterer begivenheden: %s " %(event_to_create.title))

            #Creating new event
            is_Recurring = event_to_create.is_recurring #TODO: Gør via variable
            if is_Recurring:
                rlt = self.aulamanager.createRecuringEvent(event_to_create)
            else:
                rlt = self.aulamanager.createSimpleEvent(event_to_create)

            if rlt is None:
                event_to_create.creation_or_update_errors.event_not_update_or_created = True

            if event_to_create.creation_or_update_errors.event_not_update_or_created == True or len(event_to_create.creation_or_update_errors.attendees_not_found)>0:
                events_with_errors.append(event_to_create)

            #Hvis begivenheden blev oprettet korrekt, da tilføjes der en optegnelse til SQL databasen
            #if not rlt is None:
                #mdbManager.update_event_record(event_to_create.outlook_global_appointment_id,rlt)
        
        if len(events_with_errors)>0:
            self.outlookmanager.send_a_aula_creation_or_update_error_mail(events_with_errors)
            self.signals.update_status.emit("%s handlinger mislykkedes. Se log for detaljer " %(str(events_with_errors)))
        else:
            #self.signals.update_status.emit("%s oprettet, %s opdateret og %s fjernet"%(str(len(changes['events_to_create']))),str(len(changes['events_to_update'])),str(len(changes['events_to_remove'])))
            self.signals.update_status.emit(f"{len(changes['events_to_create'])} oprettet, {len(changes['events_to_update'])} opdateret og {len(changes['events_to_remove'])} fjernet")


        #for errobj in events_with_errors:
            #print(errobj.title)
            #print(len(errobj.creation_or_update_errors.attendees_not_found))

    def __from_outlookobject_to_aulaevent(self,outlookobject):

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
        aula_event.outlook_global_appointment_id = outlookobject["appointmentitem"].GlobalAppointmentID
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

    def compare_calendars(self, begin, end, force_update_existing_events = False):
        #Summary of changes
        self.logger.info(" ")
        self.logger.info("..:: Sammenligner Outlook og AULA kalenderne :: ...")
        self.logger.info("Mellem datoerne")
        self.logger.info(" Start: %s" %(begin.strftime('%Y-%m-%d')))
        self.logger.info(" End: %s" %(end.strftime('%Y-%m-%d')))
        self.logger.info(" ")

        if(begin.strftime('%Y-%m-%d') < dt.datetime.today().strftime('%Y-%m-%d')):
            self.logger.critical("Kritisk fejl: Start datoen skal være senest dags dato.")
            sys.exit()

        #Finds all events from Outlook
        from datetime import timedelta
        self.signals.outlook_status.emit("Modtager begivenheder fra Outlook")
        aulaevents_from_outlook = self.outlookmanager.get_aulaevents_from_outlook(begin, end)
        self.signals.outlook_status.emit("Afsluttet")


        #Finds AULA events from ICal-calendar
        #aulabegin = dt.datetime(year=begin.year,month=begin.month,day=begin.day) #+ dt.timedelta(days=-1)
        #aulaend = dt.datetime(year=end.year,month=end.month,day=end.day-1)

        self.signals.aula_status.emit("Modtager begivenheder fra AULA")
        outlookevents_from_aula = self.aulamanager.getEvents(begin,end,is_in_daylight=self.outlookmanager.is_in_daylight(begin))
        self.signals.aula_status.emit("Afsluttet")

        #events = self.getEvents(None, None)
        

        events_to_create = []
        events_to_remove = []
        events_to_update = []

        self.logger.info("..:: ÆNDRINGER :: ...")



        #Springer over OUTLOOK begivenheder der ligger med start dato før d.d.
        events_to_keep = {}
        for key in aulaevents_from_outlook:
            dateobj = aulaevents_from_outlook[key]["appointmentitem"].start.replace(tzinfo=pytz.UTC)

            if dateobj <= dt.datetime.today().replace(tzinfo=pytz.UTC):
                self.logger.info("Outlook begivenheden \"%s\" der begynder \"%s\" er fra før nu. Springer over." %(aulaevents_from_outlook[key]["appointmentitem"].subject, aulaevents_from_outlook[key]["appointmentitem"].start))
                continue
            #SE DE FORSKELLIGE STATES: https://learn.microsoft.com/en-us/office/vba/api/outlook.olrecurrencestate og https://learn.microsoft.com/en-us/office/vba/api/outlook.appointmentitem.recurrencestate
            if aulaevents_from_outlook[key]["appointmentitem"].IsRecurring and aulaevents_from_outlook[key]["appointmentitem"].RecurrenceState == 2:
                self.logger.info("OBS: Outlook begivenheden \"%s\" er et tilbagevendende element i en serie. Denne serie er oprettet tidligere" %(aulaevents_from_outlook[key]["appointmentitem"].subject))
                continue

            if aulaevents_from_outlook[key]["appointmentitem"].IsRecurring and aulaevents_from_outlook[key]["appointmentitem"].GetRecurrencePattern().RecurrenceType == 5:
                self.logger.info("OBS: Outlook begivenheden \"%s\" der begynder \"%s\" er indstillet til at blive gentaget årlig. Dette er pt. ikke understøttet af AULA! Derfor vil begivenheden ikke blive oprettet.." %(aulaevents_from_outlook[key]["appointmentitem"].subject, aulaevents_from_outlook[key]["appointmentitem"].start))
                continue

            events_to_keep[key] = self.__from_outlookobject_to_aulaevent(aulaevents_from_outlook[key]) #Hvis begivenheden er d.d. eller senere, da overføres til denne liste.

        aulaevents_from_outlook = events_to_keep #Renavngives listen.

        #Springer over AULA begivenheder der ligger med start dato før d.d.
        events_to_keep = {}
        for key in outlookevents_from_aula:

            date_string = outlookevents_from_aula[key]["appointmentitem"].start
            dateobj = dt.datetime.strptime(date_string,'%Y-%m-%dT%H:%M:%S%z') #2020-08-10T10:05:00+00:00
            dateobj = dateobj + dt.timedelta(hours=2)

            if dateobj <= dt.datetime.today().replace(tzinfo=pytz.UTC):
                self.logger.info("AULA begivenheden \"%s\" der begynder \"%s\" er fra før nu. Springer over." %(outlookevents_from_aula[key]["appointmentitem"].subject, outlookevents_from_aula[key]["appointmentitem"].start))
                continue

            events_to_keep[key] = outlookevents_from_aula[key] #Hvis begivenheden er d.d. eller senere, da overføres til denne liste.

        outlookevents_from_aula = events_to_keep#Renavngives listen.


        # TJEKKER FOR DULETTER FRA AULA. Altså samme begivenhed er oprettet flere gange. Hvis da, da fjernes den ene udgave.
        for key in outlookevents_from_aula:
            if outlookevents_from_aula[key]["isDuplicate"] == True:
                events_to_remove.append(outlookevents_from_aula[key])
                self.logger.info("Begivenheden \"%s\" der begynder \"%s\" er en dublet. Den ekstra optegnelse vil blive fjenet fra AULA." %(outlookevents_from_aula[key]["appointmentitem"].subject, outlookevents_from_aula[key]["appointmentitem"].start))

        #Checking for events that has been updated or needs to be forced updated, and exists both places
        for key in aulaevents_from_outlook:
            if  key in outlookevents_from_aula:
                
                #If forceupdate is enabled
                if force_update_existing_events == True:
                    self.logger.info("Begivenheden \"%s\" vil blive tvunget opdateret." %(outlookevents_from_aula[key]["appointmentitem"].subject))

                    #Adds AULA eventid to array
                    aulaevents_from_outlook[key].id = outlookevents_from_aula[key]["appointmentitem"].aula_id
                    events_to_update.append(aulaevents_from_outlook[key]) 

                    #Prevents the same event to be set en both update metods. 
                    continue
  
                #If event has been updated, but force update is not set.
                if str(aulaevents_from_outlook[key].outlook_last_modification_time) != outlookevents_from_aula[key]["outlook_LastModificationTime"]:
                    #events_to_remove.append(outlookevents_from_aula[key])
                    self.logger.info("Begivenhden \"%s\" er blevet opdateret i Outlook. Vil forsøge, at opdatere på AULA." %(outlookevents_from_aula[key]["appointmentitem"].subject))
                    self.logger.debug(" - LastModificationTime fra AULA: %s" %(outlookevents_from_aula[key]["outlook_LastModificationTime"]))
                    self.logger.debug(" - LastModificationTime fra Outlook: %s" %(aulaevents_from_outlook[key].outlook_last_modification_time))
                    self.logger.debug(" - Outlook begivenhed GlobalAppointmentID: %s" %(aulaevents_from_outlook[key].outlook_global_appointment_id))
                    self.logger.debug(" - AULA begivenhed GlobalAppointmentID: %s" %(outlookevents_from_aula[key]["outlook_GlobalAppointmentID"]))
                    #events_to_remove.append(outlookevents_from_aula[key])
                    #events_to_create.append(aulaevents_from_outlook[key]) 

                    #Adds AULA eventid to array
                    aulaevents_from_outlook[key].id = outlookevents_from_aula[key]["appointmentitem"].aula_id
                    events_to_update.append(aulaevents_from_outlook[key]) 

        #Checking for events that currently only exists in Outlook and should be created in AULA
        for key in aulaevents_from_outlook:
            if not key in outlookevents_from_aula:
                events_to_create.append(aulaevents_from_outlook[key])
                self.logger.info("Begivenheden \"%s\" der begynder \"%s\" findes ikke i AULA. Vil blive oprettet i AULA." %(aulaevents_from_outlook[key].title, aulaevents_from_outlook[key].start_date))

        #Checking for events that currently only exists in AULA, and therefore should be deleted from AULA. 
        for key in outlookevents_from_aula:

            if not key in aulaevents_from_outlook:
                if not key in events_to_remove:
                    events_to_remove.append(outlookevents_from_aula[key])
                    self.logger.info("Begivenheden \"%s\" der begynder \"%s\" findes kun i AULA. Vil blive fjernet fra AULA." %(outlookevents_from_aula[key]["appointmentitem"].subject, outlookevents_from_aula[key]["appointmentitem"].start))

        #Summary of changes
        result_text = f"Status: {len(events_to_create)} oprettes, {len(events_to_update)} opdateres, {len(events_to_remove)} fjernes fra AULA"
        #self.signals.status.emit(result_text)

        self.logger.info(" ")
        self.logger.info("..:: OPSAMLING AF ÆNDRIGNER :: ...")
        self.logger.info("Begivenheder der skal oprettes: %s" %(len(events_to_create)))
        self.logger.info("Begivenheder der skal opdateres: %s" %(len(events_to_update)))
        self.logger.info("Begivenheder der skal fjernes: %s" %(len(events_to_remove)))
        self.logger.info(" ")

        #time.sleep(10)

        return {
                'events_to_create': events_to_create,
                'events_to_remove': events_to_remove,
                'events_to_update' : events_to_update
                }
