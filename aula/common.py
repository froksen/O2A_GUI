import re

def findRecipient(recipient_name, profile_id, profile_institution_code, aula_api_url, session):
    url = aula_api_url

    params = {
        'method': 'search.findRecipients',
        "text": recipient_name,
        "query": recipient_name,
        "id": str(profile_id),
        "typeahead": "true",
        "limit": "100",
        "scopeEmployeesToInstitution" : "true",
        "instCode": str(profile_institution_code),
        "fromModule":"event",
        "docTypes[]":"Profile",
        "docTypes[]":"Group"
        }

    #url = " https://www.aula.dk/api/v11/?method=search.findRecipients&text=Stefan&query=Stefan&id=779467&typeahead=true&limit=100&scopeEmployeesToInstitution=false&fromModule=event&instCode=537007&docTypes[]=Profile&docTypes[]=Group"
    url = url+"?method=search.findRecipients&text="+recipient_name+"&query="+recipient_name+"&id="+str(profile_id)+"&typeahead=true&limit=100&scopeEmployeesToInstitution=true&fromModule=event&instCode="+str(profile_institution_code)+"&docTypes[]=Profile&docTypes[]=Group"
    
    response  = session.get(url, params=params).json()
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
        
def teams_url_fixer(text):
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
            self.logger.info("Microsoft Teams meeting fundet. Fikser urls.")

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

def url_fixer(text):
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