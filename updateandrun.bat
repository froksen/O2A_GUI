chcp 65001

echo off
cls
cd /D "%~dp0"
echo ************************************
echo *          O2A OPDATERING          *
echo ************************************

echo "TRIN 1: Henter nyeste version"
git pull
echo "TRIN 2: Opretter VENV-miljø"
python -m venv venv
echo "TRIN 3 - Aktiverer VENV"
call venv\Scripts\activate.bat
echo "TRIN 4: Installerer nødvendige afhængigheder
pip install -r requirements.txt
echo "TRIN 5: Afvikler programmet"
python src\main.py