TITLE Outlook2Aula - Opdateringsprogrammet
chcp 65001

echo off
cls
cd /D "%~dp0"
echo ************************************
echo *          O2A OPDATERING          *
echo ************************************

echo "TRIN 1: Henter nyeste version"
git fetch --all
git reset --hard origin/master
echo "TRIN 2: Undersøger om VENV-miljø findes"
if exist venv\ (
  echo "- VENV-miljø blev fundet. Fortsætter"
) else (
  echo "- VENV-miljø blev ikke fundet. Opretter VENV-miljø"
  py -m venv venv
)
echo "TRIN 3 - Aktiverer VENV"
call venv\Scripts\activate.bat
echo "TRIN 4: Installerer nødvendige afhængigheder
py -m pip install -r requirements.txt
echo "TRIN 5: Afvikler programmet"
cd /D "%~dp0"
start main.pyw
