@echo off
rem install.bat — dobbeltklik for at installere Outlook2Aula.
rem Kræver ikke administratorrettigheder.
setlocal
cd /D "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
echo.
echo Tryk på en tast for at lukke dette vindue...
pause >nul
