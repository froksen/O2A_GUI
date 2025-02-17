import aula
import logging
import aula.aula_event
from setupmanager import SetupManager

if __name__ == "__main__":
 #LOGGING SETUP
    logger = logging.getLogger('O2A')
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler('o2a.log')
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)



    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fs = '%(asctime)s - %(levelname)s - %(message)s'
    gui_formatter = logging.Formatter(fs)
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    logger.info('O2A startet')


    setupmgr = SetupManager()
    username = setupmgr.get_aula_username()
    password = setupmgr.get_aula_password()


    response = aula.AulaConnection()
    response.login(username=username,password=password)

    aula_event = aula.AulaEvent()
    aula_event.title ="TEST"
    aula_event.start_date = "2024-10-31"
    aula_event.start_date_time = "2024-11-01T22:00:00.0000+01:00"
    aula_event.start_time="22:00:45"

    aula_event.end_date = "2024-10-31"
    aula_event.end_date_time = "2024-11-01T22:30:00.0000+01:00"
    aula_event.end_time="22:30:45"

    aula_event.description = "BESKRIVELSE"
    aula_event.attendee_ids = []

    aula_calendar = aula.AulaCalendar(response)

    
    aula_calendar.createSimpleEvent(aula_event)

    

            #self.updateEvent(287982478,"222NyTitel1","Min seje beskrivelse","2021-10-03T10:10:00.0000+02:00","2021-10-03T11:00:00.0000+02:00",[],False,False,True,False)

#response.login(username="olex3397@skolens.net",password="AkselJohannes2020")