import aula
import logging
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
    print(response.ProfileinstitutionCode)
#response.login(username="olex3397@skolens.net",password="AkselJohannes2020")