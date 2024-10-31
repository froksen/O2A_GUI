# This Python file uses the following encoding: utf-8
import requests                 # Perform http/https requests
from bs4 import BeautifulSoup   # Parse HTML pages
import re
import logging
import json

class LoginStatus:
    def __init__(self):
        self.status = False
        self.error_messages = []
        self.username = ""

class AulaConnection:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.logger = logging.getLogger('O2A')
        self.__profilesByLogin = ""


    def setProfilesByLogin(self,profile):
        self.__profilesByLogin = profile

    def getProfilesByLogin(self):
        return self.__profilesByLogin

    @property
    def ProfileinstitutionCode(self):
        profiles = self.getProfilesByLogin()['data']['profiles']

        for profile in profiles:
            if profile['institutionProfiles'][0]['role'] == "employee":
                return profile['institutionProfiles'][0]['institutionCode']

        def getProfileId(self):
            profiles = self.getProfilesByLogin()['data']['profiles']

            for profile in profiles:
                if profile['institutionProfiles'][0]['role'] == "employee":
                    return profile['institutionProfiles'][0]['id']

        #return self.getProfilesByLogin()['data']['profiles'][0]['institutionProfiles'][0]['id']



    def getAulaApiUrl(self):
        return 'https://www.aula.dk/api/v20/'


    def login(self,username,password) -> LoginStatus:
        #Tjekker hvilken login-metode der anvendes.
        sonderborg_idp_pattern = r'^\w\w\w\w\w\w\w\w@skolens\.net$'
        if re.match(sonderborg_idp_pattern,username):
            return self.login_with_idp(username,password)

        return self.login_with_stil(username,password)

    def find_unilogin_button(self, session_response,session):
        counter = 0
        success = False
        self.logger.info("Vælger UNI-LOGIN som login-mulighed")

        url = 'https://login.aula.dk/auth/login.php?type=unilogin'

        while success == False and counter < 10:
            try:
                # Parse response using BeautifulSoup
                soup = BeautifulSoup(session_response.text, "html.parser")
                # Get destination of form element (assumes only one)
                url = soup.form['action']   
                data = {}
                data['selectedIdp'] = "uni_idp"
                            
                if data:
                    print("TRYKKER SUBMIT")
                    response = session.post(url, data=data)
                    success = True
                # If there's no data, just try to post to the destination without data
                else:
                    response = session.post(url)
                # If the url of the response is the Aula front page, loop is exited

            # If some error occurs, try to just ignore it
            except:
                pass
            # One is added to counter each time the loop runs independent of outcome
            counter += 1
            print("TRYKKER FÆRDIG")

            return response        

    def login_with_idp(self, username, password):


        login_response = LoginStatus()

        # Start requests session
        session = self.getSession()
            
        # Get login page
        try:
            url = 'https://login.aula.dk/auth/login.php?type=unilogin'
            response = self.session.get(url)
        except requests.exceptions.ConnectionError as e:
            self.logger.critical("Det var ikke muligt, at oprette forbindelse til UNI-login dialogen")
            self.logger.critical(e)

            login_response.status = False
            login_response.username = username
            login_response.error_messages.append("Det var ikke muligt, at oprette forbindelse til UNI-login dialogen")

            return login_response

        session_response = self.find_unilogin_button(response,session)
        response = session_response

        # Login is handled by a loop where each page is first parsed by BeautifulSoup.
        # Then the destination of the form is saved as the next url to post to and all
        # inputs are collected with special cases for the username and password input.
        # Once the loop reaches the Aula front page the loop is exited. The loop has a
        # maximum number of iterations to avoid an infinite loop if something changes
        # with the Aula login.
        counter = 0
        success = False
        print("TRYKKER LOGGERIND")

        self.logger.info("Forsøger at logge på AULA...")
        while success == False and counter < 10:
            try:
                # Parse response using BeautifulSoup
                soup = BeautifulSoup(response.text, "html.parser")
                # Get destination of form element (assumes only one)
                #print(soup)
                url = soup.form['action']   

                
                
                # If form has a destination, inputs are collected and names and values
                # for posting to form destination are saved to a dictionary called data
                if url:
                    #Prints if any errors on login-dialog is present
                    login_errors = soup.find_all("span", {"class": "form-error-message"})

                    for login_error in login_errors:
                        self.logger.critical("UNI-LOGIN Fejlmeddelelse: " + str(login_error.text))
                        login_response.error_messages.append("UNI-Login error message: " + str(login_error.text))
                        counter = 10 #Breaks the loop. TODO: MAKE Pythonic

                    # Get all inputs from page
                    inputs = soup.find_all('input')

                    # Check whether page has inputs
                    if inputs:
                        # Create empty dictionary 
                        data = {}
                        # Loop through inputs
                        for input in inputs:
                            # Some inputs may have no names or values so a try/except
                            # construction is used.
                            try:
                                # Save username if input is a username field
                                if input['name'] == 'username':
                                    data[input['name']] = username
                                    self.logger.debug("Login-field: Username FOUND")
                                # Save password if input is a password field
                                elif input['name'] == 'UserName':
                                    data[input['name']] = username
                                    self.logger.debug("Login-field: IDP Username FOUND")
                                # Save password if input is a password field
                                elif input['name'] == 'Password':
                                    data[input['name']] = password
                                    self.logger.debug("Login-field: IDP Password FOUND")
                                #Selects login type, as employee this is "MEDARBEJDER_EKSTERN"
                                elif input['name'] == 'selected-aktoer':
                                    data[input['name']] = "MEDARBEJDER_EKSTERN"
                                    self.logger.debug("UNI-Login: role FOUND (Employee)")
                                # For all other inputs, save name and value of input
                                else:
                                    data[input['name']] = input['value']
                            # If input has no value, an error is caught but needs no handling
                            # since inputs without values do not need to be posted to next
                            # destination.
                            except:
                                pass

                    # If there's data in the dictionary, it is submitted to the destination url
                    if data:
                        if "Password" in data and "UserName" in data:
                            url = f"https://psso.sonderborg.dk/{soup.form['action']}" 
                            response = session.post(url, data=data)
                        else:
                            response = session.post(url, data=data)
                    # If there's no data, just try to post to the destination without data
                    else:
                        response = session.post(url)
                    # If the url of the response is the Aula front page, loop is exited
                    if response.url == 'https://www.aula.dk:443/portal/':
                        success = True
            # If some error occurs, try to just ignore it
            except:
                pass
            # One is added to counter each time the loop runs independent of outcome
            counter += 1
        
        # Login succeeded without an HTTP error code and API requests can begin 
        if success == True and response.status_code == 200:
            self.logger.info("Login var succesfuldt!")


            params = {
                    'method': 'profiles.getProfilesByLogin'
                    }
            # Perform request, convert to json and print on screen
            response_profile = session.get(self.getAulaApiUrl(), params=params).json()
            self.setProfilesByLogin(response_profile)

            # Csrfp-token is manually added to session headers.
            session.headers['csrfp-token'] = session.cookies['Csrfp-Token']


            #Setting information for response
            login_response.status = True
            login_response.username = username

            return login_response

        # Login failed for some unknown reason
        else:
            self.logger.critical("Login mislykkes!")

            #Setting information for response
            login_response.status = False
            login_response.username = username
            return login_response


    def login_with_stil(self, username, password):
        login_response = LoginStatus()

        # Start requests session
        session = self.getSession()
            
        # Get login page
        try:
            url = 'https://login.aula.dk/auth/login.php?type=unilogin'
            response = self.session.get(url)
        except requests.exceptions.ConnectionError as e:
            self.logger.critical("Det var ikke muligt, at oprette forbindelse til UNI-login dialogen")
            self.logger.critical(e)

            login_response.status = False
            login_response.username = username
            login_response.error_messages.append("Det var ikke muligt, at oprette forbindelse til UNI-login dialogen")

            return login_response

        session_response = self.find_unilogin_button(response,session)
        response = session_response

        # Login is handled by a loop where each page is first parsed by BeautifulSoup.
        # Then the destination of the form is saved as the next url to post to and all
        # inputs are collected with special cases for the username and password input.
        # Once the loop reaches the Aula front page the loop is exited. The loop has a
        # maximum number of iterations to avoid an infinite loop if something changes
        # with the Aula login.
        counter = 0
        success = False
        print("TRYKKER LOGGERIND")

        self.logger.info("Forsøger at logge på AULA...")
        while success == False and counter < 10:
            try:
                # Parse response using BeautifulSoup
                soup = BeautifulSoup(response.text, "html.parser")
                # Get destination of form element (assumes only one)
                #print(soup)
                url = soup.form['action']   

                # If form has a destination, inputs are collected and names and values
                # for posting to form destination are saved to a dictionary called data
                if url:
                    #Prints if any errors on login-dialog is present
                    login_errors = soup.find_all("span", {"class": "form-error-message"})

                    for login_error in login_errors:
                        self.logger.critical("UNI-LOGIN Fejlmeddelelse: " + str(login_error.text))
                        login_response.error_messages.append("UNI-Login error message: " + str(login_error.text))
                        counter = 10 #Breaks the loop. TODO: MAKE Pythonic

                    # Get all inputs from page
                    inputs = soup.find_all('input')

                    # Check whether page has inputs
                    if inputs:
                        # Create empty dictionary 
                        data = {}
                        # Loop through inputs
                        for input in inputs:
                            # Some inputs may have no names or values so a try/except
                            # construction is used.
                            try:
                                # Save username if input is a username field
                                if input['name'] == 'username':
                                    data[input['name']] = username
                                    self.logger.debug("Login-field: Username FOUND")
                                # Save password if input is a password field
                                elif input['name'] == 'password':
                                    data[input['name']] = password
                                    self.logger.debug("Login-field: password FOUND")
                                #Selects login type, as employee this is "MEDARBEJDER_EKSTERN"
                                elif input['name'] == 'selected-aktoer':
                                    data[input['name']] = "MEDARBEJDER_EKSTERN"
                                    self.logger.debug("UNI-Login: role FOUND (Employee)")
                                # For all other inputs, save name and value of input
                                else:
                                    data[input['name']] = input['value']
                            # If input has no value, an error is caught but needs no handling
                            # since inputs without values do not need to be posted to next
                            # destination.
                            except:
                                pass

                    # If there's data in the dictionary, it is submitted to the destination url
                    if data:
                        response = session.post(url, data=data)
                    # If there's no data, just try to post to the destination without data
                    else:
                        response = session.post(url)
                    # If the url of the response is the Aula front page, loop is exited
                    if response.url == 'https://www.aula.dk:443/portal/':
                        success = True
            # If some error occurs, try to just ignore it
            except:
                pass
            # One is added to counter each time the loop runs independent of outcome
            counter += 1
        
        # Login succeeded without an HTTP error code and API requests can begin 
        if success == True and response.status_code == 200:
            self.logger.info("Login var succesfuldt!")


            params = {
                'method': 'profiles.getProfilesByLogin'
                }
            response_profile = session.get(self.getAulaApiUrl(), params=params).json()
            self.setProfilesByLogin(response_profile)

            # Csrfp-token is manually added to session headers.
            session.headers['csrfp-token'] = session.cookies['Csrfp-Token']

            #Setting information for response
            login_response.status = True
            login_response.username = username

            return login_response

        # Login failed for some unknown reason
        else:
            self.logger.critical("Login mislykkes!")

            #Setting information for response
            login_response.status = False
            login_response.username = username
            return login_response
        
    def getSession(self):
        return self.session