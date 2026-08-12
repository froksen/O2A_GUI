@echo off
cd /D "%~dp0"
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start pythonw launcher.pyw
    goto :eof
)
rem pythonw ikke på PATH endnu (fx lige installeret) — led efter en per-bruger Python-installation
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\pythonw.exe" (
        start "" "%%D\pythonw.exe" launcher.pyw
        goto :eof
    )
)
echo Kunne ikke finde Python. Kør install.bat, eller log af og på Windows og prøv igen.
pause
