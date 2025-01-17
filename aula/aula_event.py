
class AulaEventCreationErrors:
    def __init__(self) -> None:
        self.attendees_not_found = []
        self.event_not_update_or_created = False
        self.event_has_errors = False
        self.event_not_deleted = False
    

   # @property
   # def attendees_not_found(self):
  #      return self.attendees_not_found

   # @attendees_not_found.setter
   # def attendees_not_found(self,attendee):
   #     self.event_has_errors = True
    #    self._attendees_not_found.append(attendee)

    #@property
    #ef event_not_update_or_created(self) -> bool:
    #    return self.event_not_update_or_created

    #@event_not_update_or_created.setter
    #def event_not_update_or_created(self, status=True):
    #    self.event_not_update_or_created = status
    #    self.event_has_errors = True

class AulaEvent():    
    def __init__(self) -> None:
        self.id = ""
        self.outlook_global_appointment_id = ""
        self.outlook_last_modification_time = ""
        self.attendee_ids = []
        self.outlook_required_attendees = []
        self.outlook_organizer = ""
        self.institution_code = ""
        self.creator_inst_profile_id = ""
        self.response_required = True
        self.title = ""
        self.type = ""
        self.description = ""
        self.outlook_body = ""
        self.location = ""
        self.start_date = ""
        self.end_date = ""
        self.start_time = ""
        self.end_time = ""
        self.start_timezone = ""
        self.end_timezone = ""
        self.start_date_time = ""
        self.end_date_time = ""
        self.all_day = False
        self.private = False
        self.is_recurring = False
        self.hide_in_own_calendar = False
        self.add_to_institution_calendar = False
        self.is_private = False
        self.max_date = ""
        self.interval = False
        self.week_mask = []
        self.recurrence_pattern = []
        self.aula_recurrence_pattern = []
        self.day_of_week_mask_list = []

        #NON-AULA-Properties. Used internal.
        self.creation_or_update_errors = AulaEventCreationErrors()
        self.has_errors = False
        self.has_update = False


    @property
    def start_date_time(self):
        if self.all_day == True:
            self.start_date_time = str(self.start_date).replace("/","-")  # FORMAT: 2021-05-18
        else:
            self.start_date_time = str(self.start_date).replace("/","-") + "T" + self.start_time + self.start_timezone  # FORMAT: 2021-05-18T15:00:00+02:00

        return self._start_date_time

    @start_date_time.setter
    def start_date_time(self,txt):
        self._start_date_time = txt

    @property
    def end_date_time(self):
        if self.all_day == True:
            self.end_date_time = str(self.end_date).replace("/","-")  # FORMAT: 2021-05-18T15:00:00+02:00 2021-05-20
        else:
            self.end_date_time = str(self.end_date).replace("/","-") + "T" + self.end_time + self.end_timezone # FORMAT: 2021-05-18T15:00:00+02:00 2021-05-20T19:45:01T+02:00

        return self._end_date_time

    @end_date_time.setter
    def end_date_time(self,txt):
        self._end_date_time = txt

    @property
    def description(self):
        self.description = "<p style=\"font-size:8pt;\">Begivenheden er oprettet via Outlook2Aula. Undlad at ændre i begivenheden manuelt i AULA. <br> o2a_outlook_GlobalAppointmentID=%s | o2a_outlook_LastModificationTime=%s <br>----<p>%s</p>  " %(self.outlook_global_appointment_id,self.outlook_last_modification_time,self.outlook_body)
        return self._description

    @description.setter
    def description(self,txt):
        txt = txt.replace("\r\n","<br>")
        self._description = txt 
