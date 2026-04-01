@echo off
SETLOCAL

:: CONFIGURATION
set APP_DIR="O2A"
set GIT_REPO=https://github.com/froksen/O2A_GUI.git
set SCRIPT_NAME=main.pyw
set PYTHON_EXE=python  :: or python3, depending on your install

:: Step 1: Clone or update repo
IF NOT EXIST "%APP_DIR%" (
    echo Cloning repository...
    git clone %GIT_REPO% %APP_DIR%
) ELSE (
    echo Updating repository...
    cd /d %APP_DIR%
    git pull
)

:: Step 2: Set up virtual environment
cd /d %APP_DIR%
IF NOT EXIST "venv" (
    echo Creating virtual environment...
    %PYTHON_EXE% -m venv venv
)

:: Step 3: Install dependencies
echo Installing dependencies...
venv\Scripts\pip install --upgrade pip
venv\Scripts\pip install -r requirements.txt

:: Step 4: Run the script
echo Starting the script...
venv\Scripts\python %SCRIPT_NAME%

ENDLOCAL
pause
