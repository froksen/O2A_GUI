import win32com.client
import datetime as dt
from datetime import timedelta
import re
import sys
import logging
import time
import os

class OutlookManager:
    def __init__(self):
        print("Outlook Manager Initialized")
        self.logger = logging.getLogger('O2A')


    def is_in_daylight(self, date_to_check):
        #TODO: Find en smartere måde, at lave dette tjek på!
        daylight_periods = [
                {
                    "start": dt.datetime(2021,3,28), #Den første dag i sommertid
                    "end" : dt.datetime(2021,10,30) #Den sidste dag i sommertid
                },
                {
                    "start": dt.datetime(2022,3,27), #Den første dag i sommertid
                    "end" : dt.datetime(2022,10,29) #Den sidste dag i sommertid
                },
                {
                    "start": dt.datetime(2023,3,26), #Den første dag i sommertid
                    "end" : dt.datetime(2023,10,28) #Den sidste dag i sommertid
                },
                {
                    "start": dt.datetime(2024,3,31), #Den første dag i sommertid
                    "end" : dt.datetime(2024,10,27) #Den sidste dag i sommertid
                },
                {
                    "start": dt.datetime(2025,3,30), #Den første dag i sommertid
                    "end" : dt.datetime(2025,10,26) #Den sidste dag i sommertid
                },
            ]

        is_daylight = False
        for daylight_period in daylight_periods:
            if date_to_check <= daylight_period["end"] and date_to_check >= daylight_period["start"]:
                is_daylight = True
                break

        return is_daylight

    def get_aulaevents_from_outlook(self,begin,end):

        def get_aula_timezone(outlook_date_time):

            outlook_date_time = str(outlook_date_time)
            date_part = outlook_date_time.split(" ")[0]
            date_part = date_part.split("-")

            year = int(date_part[0])
            month = int(date_part[1])
            day = int(date_part[2])

            mDate = dt.datetime(year,month,day)

            if self.is_in_daylight(mDate):
                return "+02:00"
            else:
                return "+01:00"

        def format_as_aula_date(outlook_date_time):
            outlook_date_time = str(outlook_date_time)
            date_part = outlook_date_time.split(" ")[0]
            date_part = date_part.split("-")

            date_part = date_part[2]+"/"+date_part[1]+"/"+date_part[0] 

            return date_part.strip()

        def format_as_aula_time(outlook_date_time):
            outlook_date_time = str(outlook_date_time)
            time_part = outlook_date_time.split(" ")[1]
            time_part = time_part.split(":")
            time_part = time_part[0] + ":" + time_part[1]
            return time_part.strip()
            #2021-03-04 10:00:00+00:00

        aulaEvents = {}

        events = self.get_personal_calendar(begin,end) #Finds all events
        
        self.logger.info("Reading Outlook events")
        for event in events: #Loops through
            categories_org = event.categories.split(";") #If event has multiple categories, then split

            #Makes sure that there are no whitespaces before or after
            categories = []
            for category in categories_org:
                #print(category)
                categories.append(str(category).strip())

            # If has category "AULA" then it should be added to AULA
            if 'AULA' in categories or 'AULA Institutionskalender' in categories:
                addToInstitutionCalendar = False
                hideInOwnCalendar = False

                if not 'AULA' in categories and 'AULA Institutionskalender' in categories:
                    hideInOwnCalendar = True

                #If it also has category "AULA: Institutionskalender" then the event should be added to the instituionCalendar
                if 'AULA Institutionskalender' in categories: #Loops through categories
                    addToInstitutionCalendar = True

                #Fixes issue, where end in Allday events are pushed one day forward.
                #TODO: Make a better fix. 
                if event.AllDayEvent == True:
                    try:
                        #pass
                        endDateTime_fix = event.end - timedelta(days=1)
                        event.end = endDateTime_fix

                        #startDateTime_fix = event.start - timedelta(days=1)
                        #event.start = startDateTime_fix
                    except: 
                        pass
                        #print("SKIPPED")

                if event.GlobalAppointmentID in aulaEvents:
                    self.logger.info(f'Outlook mananger: Event with title "{event.subject}" and uid "{event.GlobalAppointmentID}" is already found in Outlook. Skipping')
                    continue

                GlobalAppointmentID = event.GlobalAppointmentID

                if event.IsRecurring:
                    event_start = str(event.start).replace(" ","")
                    event_end = str(event.end).replace(" ","")
                    GlobalAppointmentID = (f"{event.GlobalAppointmentID}_{event_start}_{event_end}")


                #Array containing event information
                aulaEvents[GlobalAppointmentID] = {"appointmentitem":event,
                    "outlook_GlobalAppointmentID_internal" : GlobalAppointmentID,
                    "aula_startdate": format_as_aula_date(event.start),
                    "aula_enddate": format_as_aula_date(event.end),
                    "aula_starttime": format_as_aula_time(event.start),
                    "aula_endtime": format_as_aula_time(event.end),
                    "aula_startdate_timezone" : get_aula_timezone(event.start),
                    "aula_enddate_timezone" : get_aula_timezone(event.end),
                    "hideInOwnCalendar" : hideInOwnCalendar,
                    "addToInstitutionCalendar" : addToInstitutionCalendar
                }
                
                #print("ENDDATE")
               # print(aulaEvents[event.GlobalAppointmentID]["appointmentitem"].subject)
                #print(aulaEvents[event.GlobalAppointmentID]["aula_enddate"])
                #print(event.end)
                #print(event.IsRecurring)
               # paatern = event.GetRecurrencePattern()
               # print(paatern)
                #print(paatern.RecurrenceType)
                #time.sleep(2)

        return aulaEvents

    def send_a_mail_program(self, message_to_send=""):
        #FROM: https://gist.github.com/vinovator/0a6d653c22c32ab67e11
        outlook = win32com.client.Dispatch("Outlook.Application")

        exchange_user = outlook.Session.CurrentUser.AddressEntry.GetExchangeUser()
        ownEmailAdress = exchange_user.PrimarySmtpAddress

        self.logger.debug("Exchange user " + str(exchange_user))
        self.logger.debug("Exchange user email " + ownEmailAdress)
        if ownEmailAdress == None:
            return

       #     Outlook VBA Reference 
       # 0 - olMailItem
       # 1 - olAppointmentItem
       # 2 - olContactItem
       # 3 - olTaskItem
       # 4 - olJournalItem
       # 5 - olNoteItem 
       # 6 - olPostItem
       # 7 - olDistributionListItem
        mail = outlook.CreateItem(0)

        mail.To = ownEmailAdress
        #mail.CC = "mail2@example.com"
        #mail.BCC = "mail3@example.com"

        mail.Subject = "(Outlook2Aula) Intern/programmel fejl under afvikling"

        # Using "Body" constructs body as plain text
        # mail.Body = "Test mail body from Python"

        """
        Using "HtmlBody" constructs body as html text
        default font size for most browser is 12
        setting font size to "-1" might set it to 10
        """
        mail.HTMLBody = f"""
        <html>
        <head></head>
        <body>
            <font color="Black" size=-1 face="Arial">
            <p>Kære {str(exchange_user)}!</p>
            Outlook2Aula overførselsprogrammet prøvede at køre på din computer. Der skete desværre en eller flere fejl internt i programmet, som gjorde at afviklingen mislykkes.<br><br>

            <b>Følgende fejl blev meldt:</b>
            <br><br>
            {message_to_send}
            <br>
            <br>
            Hvis denne fejl bliver ved med at blive meldt, da kontakt Ole Frandsen (olfr@sonderborg.dk). Videresend gerne denne mail direkte, da den indeholder information om fejlen. <u>Intet bliver videresendt automatisk!</u>

            <p>Venlig hilsen <br> Outlook2Aula overførselsprogrammet</p>
            </font>
        </body>
        </html>
        """

        """
        Set the format of mail
        1 - Plain Text
        2 - HTML
        3 - Rich Text
        """
        mail.BodyFormat = 2

        # Instead of sending the message, just display the compiled message
        # Useful for visual inspection of compiled message
        #mail.Display(True)

        # Send the mail
        # Use this directly if there is no need for visual inspection
        mail.Send()


    def send_a_mail(self, login_response_obj, message_to_send=""):
        #FROM: https://gist.github.com/vinovator/0a6d653c22c32ab67e11
        outlook = win32com.client.Dispatch("Outlook.Application")

        exchange_user = outlook.Session.CurrentUser.AddressEntry.GetExchangeUser()
        ownEmailAdress = exchange_user.PrimarySmtpAddress

        error_messages = login_response_obj.error_messages
        attemptet_uni_login_name = login_response_obj.username

        self.logger.debug("Exchange user " + str(exchange_user))
        self.logger.debug("Exchange user email " + ownEmailAdress)
        if ownEmailAdress == None:
            return

        error_messages_string = ""
        for error_msg in error_messages:
            error_messages_string = error_messages_string + "<li>" + str(error_msg) + "</li>"

        path_to_setup_batfile = os.path.join(os.getcwd())

       #     Outlook VBA Reference 
       # 0 - olMailItem
       # 1 - olAppointmentItem
       # 2 - olContactItem
       # 3 - olTaskItem
       # 4 - olJournalItem
       # 5 - olNoteItem 
       # 6 - olPostItem
       # 7 - olDistributionListItem
        mail = outlook.CreateItem(0)

        mail.To = ownEmailAdress
        #mail.CC = "mail2@example.com"
        #mail.BCC = "mail3@example.com"

        mail.Subject = "(Outlook2Aula) Afviklingsfejl"

        # Using "Body" constructs body as plain text
        # mail.Body = "Test mail body from Python"

        """
        Using "HtmlBody" constructs body as html text
        default font size for most browser is 12
        setting font size to "-1" might set it to 10
        """
        mail.HTMLBody = f"""
        <html>
        <head></head>
        <body>
            <font color="Black" size=-1 face="Arial">
            <p>Kære {str(exchange_user)}!</p>
            Outlook2Aula overførselsprogrammet prøvede at køre på din computer. Der skete desværre en eller flere fejl, som gjorde at afviklingen mislykkes.<br><br>

            <b>Følgende fejl blev meldt:</b>
            <ul>
            {error_messages_string}
            </ul>
            
            <p><b>Du har anvendt følgende AULA brugernavn: </b> {attemptet_uni_login_name}<br>(Kodeord ikke nævnt, af sikkerhedsmæssige årsager)</p>
            <br>
            <h4>Ændre UNI-login oplysninger?</h4>
            Hvis det er fordi du har ændret din/fået ny adgangskode eller dit brugernavn er forkert, da skal du genintaste din UNI-oplysninger i programmet.
            Du kan ændre dine UNI-login oplysninger vha. programmets opsætningsdialog. 
            <ul>
                <li>Se vejledningsvideo: <a href="{path_to_setup_batfile}/Vejledning%20-%20Opdatere%20Aula%20adgangskode.mkv">Vejledning til at opdatere Aula oplysninger</a></p></li>
            </ul>
            
             
            <br><br>
            Hvis det ikke er tilfældet, og denne fejl bliver ved med at blive meldt, da kontakt Ole Frandsen (olfr@sonderborg.dk) eller Jesper Qvist (jeqv@sonderborg.dk).

            <p>Venlig hilsen <br> Outlook2Aula overførselsprogrammet</p>
            </font>
        </body>
        </html>
        """

        """
        Set the format of mail
        1 - Plain Text
        2 - HTML
        3 - Rich Text
        """
        mail.BodyFormat = 2

        # Instead of sending the message, just display the compiled message
        # Useful for visual inspection of compiled message
        #mail.Display(True)

        # Send the mail
        # Use this directly if there is no need for visual inspection
        mail.Send()
        
    def send_a_aula_creation_or_update_error_mail(self, aula_events_with_errors):
        #FROM: https://gist.github.com/vinovator/0a6d653c22c32ab67e11
        outlook = win32com.client.Dispatch("Outlook.Application")

        exchange_user = outlook.Session.CurrentUser.AddressEntry.GetExchangeUser()
        ownEmailAdress = exchange_user.PrimarySmtpAddress

        self.logger.debug("Exchange user " + str(exchange_user))
        self.logger.debug("Exchange user email " + ownEmailAdress)
        if ownEmailAdress == None:
            return

        error_messages_string = ""
        #print(len(aula_events_with_errors))
        for aula_error in aula_events_with_errors:
            error_messages_string = error_messages_string + "<h5> Begivenheden: \"" + aula_error.title +"\" (" + aula_error.start_date_time + ") " + "</h5>"

            if aula_error.creation_or_update_errors.event_not_update_or_created == True:
                error_messages_string = error_messages_string + "FEJL: Begivenheden blev ikke oprettet.<br><br>"
            elif aula_error.creation_or_update_errors.event_not_deleted == True:
                error_messages_string = error_messages_string + "FEJL: Begivenheden blev ikke fjernet i AULA.<br><br>"
            elif len(aula_error.creation_or_update_errors.attendees_not_found)>0:
                error_messages_string = error_messages_string + "FEJL: Begivenheden blev oprettet, dog blev følgende personer blev <u>ikke</u> tilføjet til begivenheden da de ikke blev fundet på AULA <ul>"

                for person in aula_error.creation_or_update_errors.attendees_not_found:
                    error_messages_string = error_messages_string + "<li>" + str(person) + "</li>"

                error_messages_string = error_messages_string + "</ul><br>"

       #     Outlook VBA Reference 
       # 0 - olMailItem
       # 1 - olAppointmentItem
       # 2 - olContactItem
       # 3 - olTaskItem
       # 4 - olJournalItem
       # 5 - olNoteItem 
       # 6 - olPostItem
       # 7 - olDistributionListItem
        mail = outlook.CreateItem(0)

        mail.To = ownEmailAdress
        #mail.CC = "mail2@example.com"
        #mail.BCC = "mail3@example.com"

        mail.Subject = "(Outlook2Aula) Fejl ved opretelse af en eller flere begivenheder"

        path_to_personercsv = os.path.join(os.getcwd(),"personer.csv")

        path_to_ignorecsv = os.path.join(os.getcwd(),"personer_ignorer.csv")


        # Using "Body" constructs body as plain text
        # mail.Body = "Test mail body from Python"

        """
        Using "HtmlBody" constructs body as html text
        default font size for most browser is 12
        setting font size to "-1" might set it to 10
        """
        mail.HTMLBody = f"""
        <html>
        <head></head>
        <body>
            <font color="Black" size=-1 face="Arial">
            <p>Kære {str(exchange_user)}</p>
           Der skete desværre en eller flere fejl, som gjorde at oprettelsen af en eller flere begivenheder mislykkes helt eller delvist.<br><br>

            <h4>Fejl i følgende begivenheder:</h4>
            {error_messages_string}
            
            <h4>Outlook navn forskelligt fra AULA navn?</h4>
            <p>Nogle gange kan ansatte/kolleger være oplistet med forskellige navne i Outlook som i AULA. Det kan være et mellemnavn der er det ene sted men ikke det andet. For at håndtere dette, skal du udfylde de rigtige oplysninger i følgende fil: <a href="{path_to_personercsv}">{path_to_personercsv}</a></p>
            <ul>
                <li>Se vejledningsvideo: <a href="{os.getcwd()}/Vejledning%20-%20Personer%20med%20forskelligt%20navn%20fra%20Outlook%20til%20Aula.mkv">Vejledning til at indtaste personer med forskelligt navn i Aula og Outlook</a></p></li>
            </ul>

            <h4>Ignorer bestemte personer, som ikke er på AULA?</h4>
            <p>Du får en mail, hvis en person der fremgår af Outlook begivenheden ikke blev tilføjet korrekt på AULA. Dog er der nogle gange, hvor du ønsker at programmet skal ignorer at personen ikke blev tilføjet. Altså egentlig acceptere, at personen ikke blev fundet i AULA. Det kan f.eks. være hvis du ofte har eksterne kontakter på, som ikke er på AULA. Da skal du tilføje deres Outlook navn tilfølgende fil: <a href="{path_to_ignorecsv}">{path_to_ignorecsv} </p>
            <ul>
                <li>Se vejledningsvideo: <a href="{os.getcwd()}/Vejledning%20-%20Ignorer%20personer.mkv">Vejledning til at indtaste personer som skal ignoreres</a></p></li>
            </ul>

            <br><br>
            Hvis det ikke er tilfældet, og denne fejl bliver ved med at blive meldt, da kontakt Ole Frandsen (olfr@sonderborg.dk) eller Jesper Qvist (jeqv@sonderborg.dk).

            <p>Venlig hilsen <br> Outlook2Aula overførselsprogrammet</p>
            </font>
        </body>
        </html>
        """

        """
        Set the format of mail
        1 - Plain Text
        2 - HTML
        3 - Rich Text
        """
        mail.BodyFormat = 2

        # Instead of sending the message, just display the compiled message
        # Useful for visual inspection of compiled message
        #mail.Display(True)

        # Send the mail
        # Use this directly if there is no need for visual inspection
        mail.Send()
        

    def get_personal_calendar_username(self):
        outlook = win32com.client.Dispatch("Outlook.Application")
        ns = outlook.GetNamespace("MAPI")
        return ns.CurrentUser

    def get_personal_calendar(self,begin,end):
        outlook = win32com.client.Dispatch("Outlook.Application")
        ns = outlook.GetNamespace("MAPI")
        calendar = ns.GetDefaultFolder(9).Items
        calendar.IncludeRecurrences = True

        return self.__get_calendar(calendar,begin,end)
        
    def __get_calendar(self,calendar,begin,end):
        calendar.Sort('[Start]')
        restriction = "[Start] >= '" + begin.strftime('%d/%m/%Y') + "' AND [END] <= '" + end.strftime('%d/%m/%Y') + "'"
        calendar = calendar.Restrict(restriction)
        
        return calendar
