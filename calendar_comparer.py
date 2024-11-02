
class CalendarComparer:
    def __init__(self, aula_events, outlook_events):
        self._outlook_events = set(outlook_events)
        self._aula_events = set(aula_events)

    def find_unique_events(self):
        unique_to_aula = self._aula_events - self._outlook_events
        unique_to_outlook = self._outlook_events - self._aula_events
        
        return {
            'unique_to_aula': unique_to_aula,
            'unique_to_outlook': unique_to_outlook
        }

    def are_calendars_identical(self) -> bool:
            return self.calendar1 == self.calendar2