import re

def __remove_html_tags(text):
    """Remove html tags from a string"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

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