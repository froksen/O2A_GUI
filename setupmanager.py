from distutils.core import run_setup
from email import message
import getpass
from tkinter import messagebox
import tkinter
from venv import create
import keyring
import configparser
import win32com.client
import time
import sys
from tkinter import *
from tkinter import ttk
import os

class SetupManager:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.__read_config_file()

    def setup_menu_gui(self):

        def action_changepwd():
            self.run_setup_gui()

        def action_run_program():
            cwd = os.getcwd()
            print(cwd)
            dir_path = os.path.dirname(os.path.realpath(__file__))
            print(dir_path)
            print(f"{cwd}\O2A\main.py -r")

            cmd_to_run = f'python "{cwd}\src\main.py" -r'
            os.system(f'start /WAIT cmd /k {cmd_to_run}')

        def action_force_run_program():
            cwd = os.getcwd()
            print(cwd)
            dir_path = os.path.dirname(os.path.realpath(__file__))
            print(dir_path)
            print(f"{cwd}\O2A\main.py -r")

            cmd_to_run = f'python "{cwd}\src\main.py" -f -r'
            os.system(f'start /WAIT cmd /k {cmd_to_run}')

        def action_opensheet():
            cwd = os.getcwd()
            dir_path = os.path.dirname(os.path.realpath(__file__))

            cmd_to_run = f'excel.exe "{cwd}\personer.csv"'
            os.system(f'start /WAIT {cmd_to_run}')

        def action_openexplorer():
            cwd = os.getcwd()
            dir_path = os.path.dirname(os.path.realpath(__file__))

            cmd_to_run = f'explorer.exe "{cwd}"'
            os.system(f'start /WAIT {cmd_to_run}')

        mainwindow = Tk()
        mainwindow.geometry('380x200')
        mainwindow.title("O2A")
        style = ttk.Style()
        style.theme_use('clam')

        header_label = Label( mainwindow, text="O2A: Opsætning og kørsel", relief="flat", font=("Arial Bold", 20) )
        header_label.grid(column=0, row=0,columnspan=2)

        btn = Button(mainwindow, text="Indtast AULA brugernavn og kodeord", command=action_changepwd)
        btn.grid(column=0, row=1,columnspan=2)

        btn = Button(mainwindow, text="Åben programmets mappe", command=action_openexplorer)
        btn.grid(column=0, row=2,columnspan=2)
        
        btn = Button(mainwindow, text="Kør programmet", command=action_run_program)
        btn.grid(column=0, row=4,columnspan=2)

        btn = Button(mainwindow, text="Gennemtving opdatering af kalender", command=action_force_run_program)
        btn.grid(column=0, row=5,columnspan=2)


        mainwindow.mainloop()

    def run_setup_gui(self):
        #messagebox.showwarning("Sikkerhed", "Alle kodeord gemmes i dit operativsystems nøglering. Hvis en anden person eller program får adgang til din brugerkonto, da har de også adgang til dine kodeord! Brug dette program på eget ansvar!")
        self.create_outlook_categories()

        mainwindow = Tk()
        mainwindow.geometry('380x150')
        mainwindow.title("O2A Opsætningsassistent")


        header_label = Label( mainwindow, text="Aula oplysninger", relief="flat", font=("Arial Bold", 25) )
        #header_label.configure("center", justify='center')
        header_label.grid(column=0, row=0,columnspan=2)

        mainwindow.lift()

        #helptext = Label( mainwindow, text="Anvendes til at kunne læse din kalender på AULA.", relief="flat", font=("Arial Bold", 12) )
        #helptext.grid(column=0, row=1,columnspan=2)

        def save_button_clicked():

            answer = messagebox.askyesno("Gem oplysninger", "Sikker på, at du ønsker at gemme disse oplysninger?")

            if answer == True:
                try:
                    self.config.add_section("AULA")
                except configparser.DuplicateSectionError:
                    pass #If section already exists, then skip

                self.config['AULA']['username'] = username_field.get()
                keyring.set_password("o2a", "aula_password", password_field.get())
                self.__write_config_file()
                messagebox.showinfo("Aula oplysninger","Oplysningerne er blevet gemt!")
                mainwindow.quit()

            else:
                messagebox.showinfo("Aula oplysninger","Der blev ikke gemt nogle oplysninger.")


        def create_form_field(label, row, show=""):
            label = Label( mainwindow, text=label, relief="flat", font=("Arial Bold", 12) )
            entry = Entry(mainwindow,width=20, show=show)

            label.grid(column=0, row=row)
            entry.grid(column=1, row=row)

            return entry


        #Setup form
        username_field = create_form_field("UNI-brugernavn",2)
        password_field = create_form_field("UNI-kodeord",3,show="*")

        save_button = Button(mainwindow, text="Gem", command=save_button_clicked)
        save_button.grid(column=1, row=5)


        mainwindow.mainloop()

    def update_unilogin(self,username,password):
        try:
            self.config.add_section("AULA")
        except configparser.DuplicateSectionError:
            pass #If section already exists, then skip

        self.config['AULA']['username'] = username
        keyring.set_password("o2a", "aula_password", password)
        self.__write_config_file()


    def do_setup(self):
        self.__show_welcome_screen()
        self.__aula_setup()

    def __show_welcome_screen(self):
        print()
        print()
        print()
        print()
        print("..:: This is the initial setup for O2A ::..")
        print()
        print("WHY: This wizard will ask you for information that is needed to make the script work.")
        print("WHAT IF: If you misspell or make other mistakes. Run this wizard again.")
        print("SECURITY: All passwords and usernames are stored in the keyring for your operation system.")
        print("")
        input("Press <ENTER> to continue")

    def __aula_setup(self):
        print("..:: Information for AULA ::..")
        print("The following information is used to operate and login to AULA. Please enter information for UNI-login")


        usr = self.__ask_for_username()
        passwd = self.__ask_for_password()

        print("")
        print("")
        print("")
        print("")
        print("Is the following correct?")
        print("UNI-username: " + str(usr))
        print("UNI-password: " + str(passwd)) 
        print("(All passwords are stored in the keyring for your operation system.)")
        print("")
        print("")
        print("")
        
        should_save = False
        while not should_save:
            reply = str(input('Do you want to store these information? (Y)es or (N)o: ')).lower().strip()

            try:
                if reply[:1] == 'y':
                    #self.create_outlook_categories()
                    should_save = True
                if reply[:1] == 'n':
                    should_save = False
            except IndexError:
                should_save = False

            if should_save == False:
                print("Process abortet, nothing saved or changed! Rerun this setup if, you want to retype username or password.")
                sys.exit()

        try:
            self.config.add_section("AULA")
        except configparser.DuplicateSectionError:
            pass #If section already exists, then skip

        self.config['AULA']['username'] = usr
        keyring.set_password("o2a", "aula_password", passwd)

        self.__write_config_file()

        print("Username and password stored!")

        print()
        print()
        self.yes_or_no("Do you want to create necessary categories in Outlook?")

        print("AULA setup completed!")

    def store_yes_or_no(self, question):
        while "the answer is invalid":
            reply = str(input(question+' (y/n): ')).lower().strip()

            try:
                if reply[:1] == 'y':
                    #self.create_outlook_categories()
                    return True
                if reply[:1] == 'n':
                    return False
            except IndexError:
                return False

    def yes_or_no(self, question):
        while "the answer is invalid":
            reply = str(input(question+' (y/n): ')).lower().strip()

            try:
                if reply[:1] == 'y':
                    self.create_outlook_categories()
                    return True
                if reply[:1] == 'n':
                    return False
            except IndexError:
                return False

    def create_task(self):
        import os

        os.system("schtasks /CREATE /F /TN MINOPGAVE /XML task_template.xml")

    def check_outlook_categories(self):
        outlook = win32com.client.Dispatch("Outlook.Application")
        ns = outlook.GetNamespace("MAPI")
        print("Checking if Outlook has necessary categories")

        hasAula = False
        hasAULAInstitutionskalender = False
        for category in ns.Categories:
            if(category.name == "AULA"):
                hasAula = True

            if category.name == "AULA Institutionskalender":
                hasAULAInstitutionskalender = True

        if hasAula or hasAULAInstitutionskalender:
            return True
        else:
            return False

    def create_outlook_categories(self):
        outlook = win32com.client.Dispatch("Outlook.Application")
        ns = outlook.GetNamespace("MAPI")

        print("Checking if Outlook has necessary categories")
        hasAula = False
        hasAULAInstitutionskalender = False
        for category in ns.Categories:
            if(category.name == "AULA"):
                hasAula = True

            if category.name == "AULA Institutionskalender":
                hasAULAInstitutionskalender = True

        if not hasAula:
            print("Missing category 'AULA'. Will be created")
            ns.Categories.Add("AULA")
            time.sleep(1) #needed because otherwise outlook can keep up.

        if not hasAULAInstitutionskalender:
            print("Missing category 'AULA Institutionskalender'. Will be created")
            ns.Categories.Add("AULA Institutionskalender")
            time.sleep(1) #needed because otherwise outlook can keep up.

        if hasAULAInstitutionskalender and hasAula:
            print("All necessary categories was found.")
            #print(category.name)
            #print(category.CategoryID)

    def get_aula_username(self):
        return self.config['AULA']['username']

    def get_aula_password(self):
        return keyring.get_password("o2a","aula_password")

    def __read_config_file(self):
        if not os.path.isfile("configuration.ini"):
            self.update_unilogin("Ukendt","Ukendt")

        try:
            self.config.read('configuration.ini')
        except Exception:
            pass

    def __write_config_file(self):
        with open('configuration.ini', 'w') as configfile:
            self.config.write(configfile)

    def __ask_for_password(self):
        pwd = ""
        try:
            pwd = getpass.getpass(prompt='Password: ', stream=None)
        except Exception as e:
            print(e)

        return pwd

    def __ask_for_username(self):
        usr = ""
        try:
            usr = input ("Username ["+getpass.getuser()+"]:")  or getpass.getuser()
        except Exception as e:
            print(e)

        return usr

