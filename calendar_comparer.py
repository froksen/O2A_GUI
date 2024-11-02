
class CalendarComparer:
    def __init__(self, aula_calendar, outlook_calendar):
        self._outlook_calendar = outlook_calendar
        self._aula_calendar = aula_calendar

    def find_unique_events(self):
        unique_to_aula = self.__aula_events - self.__outlook_events
        unique_to_outlook = self.__outlook_events - self.__aula_events
        return {
            'unique_to_aula': unique_to_aula,
            'unique_to_outlook': unique_to_outlook
        }

    def are_calendars_identical(self) -> bool:
            """Check if the two calendars have exactly the same dates."""
            return self.calendar1 == self.calendar2