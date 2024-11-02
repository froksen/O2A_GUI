
class CalendarComparer:
    def __init__(self, outlook_events, aula_events):
        self.__aula_events = aula_events
        self.__outlook_events = outlook_events

    def find_unique_events(self):
        unique_to_aula = self.__aula_events - self.__outlook_events
        unique_to_outlook = self.__outlook_events - self.__aula_events
        return {
            'unique_to_aula': unique_to_aula,
            'unique_to_outlook': unique_to_outlook
        }
