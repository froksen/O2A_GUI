@echo off
chcp 65001 >nul
cd /D "%~dp0"

:: Saet DEBUG=1 for at springe git-opdatering over
set DEBUG=1

title Outlook2Aula
echo ************************************
echo *            O2A START             *
if "%DEBUG%"=="1" echo *          DEBUG-TILSTAND          *
echo ************************************
echo.

if "%DEBUG%"=="1" goto :venv

echo TRIN 1: Henter nyeste version
git fetch --all
git reset --hard origin/master
if errorlevel 1 (
    echo FEJL: Git-opdatering mislykkedes.
    pause ^& exit /b 1
)

:venv
echo.
echo TRIN 2: Undersoeger VENV-miljoe
if not exist venv\ (
    echo - Opretter VENV-miljoe...
    py -m venv venv
    if errorlevel 1 (
        echo FEJL: Kunne ikke oprette VENV-miljoe.
        pause ^& exit /b 1
    )
)
echo - VENV-miljoe klar.

echo.
echo TRIN 3: Installerer afhaengigheder
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo FEJL: Installation af afhaengigheder mislykkedes.
    pause ^& exit /b 1
)

:run
echo.
echo TRIN 4: Starter programmet
venv\Scripts\python.exe main.pyw
if errorlevel 1 (
    echo.
    echo FEJL: Programmet stoppede med en fejl.
    pause
)