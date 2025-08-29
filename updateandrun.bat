TITLE Outlook2Aula - Opdateringsprogrammet
chcp 65001

echo off
cls
cd /D "%~dp0"
echo ************************************
echo *          O2A OPDATERING          *
echo ************************************

echo "TRIN 1: Henter nyeste version fra Github"


:: Step 3: Install dependencies
echo "TRIN 2 Opgraderer PIP og installerer UV.....""
py -m pip install --upgrade pip
py -m pip install uv

cd /D "%~dp0"
echo "TRIN 3 Afvikler programmet.....""
start uv run main.pyw
exit