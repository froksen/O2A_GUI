import csv
import logging
import shutil

class PeopleCsvManager():    
    def __init__(self, csv_file="personer.csv", people_to_ignore="personer_ignorer.csv") -> None:
        self.logger = logging.getLogger('O2A')
        self.__people = self.__readFile(csv_file)

        self.__people_to_ignore = self.__readFile_ignore(people_to_ignore)

    def getPersonData(self,person_outlook_name):
        self.logger.debug(f"Searching for {person_outlook_name} in CSV register")

        for person in self.__people:
            if person["outlook_name"] == person_outlook_name:
                aula_name = person["aula_name"]
                self.logger.debug(f"FOUND and should be replaced with {aula_name}")
                return aula_name

        for person in self.__people_to_ignore:
            if person["outlook_name"] == person_outlook_name:
                self.logger.debug(f"FOUND and should be IGNORED")
                return "IGNORE_PERSON"

        self.logger.debug("NOT FOUND")
        return None

    def __readFile_ignore(self, csv_file="personer_ignorer.csv"):
        people = []

        try:
            with open(csv_file, mode='r') as csv_file:
                csv_reader = csv.DictReader(csv_file,delimiter=";")
                line_count = 0
                for row in csv_reader:
                    if line_count == 0:
                        self.logger.debug(f'Column names are {"; ".join(row)}')
                        line_count += 1

                    person = {
                        "outlook_name" : row["Outlook navn"],
                    }

                    people.append(person)

                    self.logger.debug(f'\t{row["Outlook navn"]}.')
                    line_count += 1

                self.logger.debug(people)
                self.logger.debug(f'Processed {line_count} lines.')
        except FileNotFoundError as e:
            self.logger.warning(f"CSV filen '{csv_file}'' blev ikke fundet. Prøver at oprette den, og genkøre sig køre igen.")
            self.logger.debug(e)

            shutil.copy2("personer_ignorer_skabelon.csv","personer_ignorer.csv")

            people=self.__readFile()

        return people

    def __readFile(self, csv_file="personer.csv"):
        people = []

        try:
            with open(csv_file, mode='r') as csv_file:
                csv_reader = csv.DictReader(csv_file,delimiter=";")
                line_count = 0
                for row in csv_reader:
                    if line_count == 0:
                        self.logger.debug(f'Column names are {"; ".join(row)}')
                        line_count += 1

                    person = {
                        "outlook_name" : row["Outlook navn"],
                        "aula_name" : row["AULA navn"]
                    }

                    people.append(person)

                    self.logger.debug(f'\t{row["Outlook navn"]} works in the {row["AULA navn"]} .')
                    line_count += 1

                self.logger.debug(people)
                self.logger.debug(f'Processed {line_count} lines.')
        except FileNotFoundError as e:
            self.logger.warning(f"CSV filen '{csv_file}'' blev ikke fundet. Prøver at oprette den, og genkøre sig køre igen.")
            self.logger.debug(e)

            shutil.copy2("personer_skabelon.csv","personer.csv")

            people=self.__readFile()

        return people

#pClass = PeopleCsvManager(csv_file="personer.csv")
#print(pClass.getPersonData("Fiktiv Fiktivsen"))