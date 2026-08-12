# install.ps1 - Forste-installation af Outlook2Aula (ingen administratorrettigheder kraevet)
#
# Installerer Python og Git per-bruger (hvis de mangler), henter programmet fra GitHub,
# opretter en genvej paa skrivebordet og starter programmet.
#
# Koeres normalt via install.bat (dobbeltklik). Kan ogsaa koeres direkte:
#   powershell -ExecutionPolicy Bypass -File install.ps1

param(
    [string]$InstallDir,
    [switch]$SkipLaunch,
    [switch]$SkipShortcut,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# -- Indstillinger -------------------------------------------------------------
$RepoUrl    = "https://github.com/froksen/O2A_GUI.git"
$Branch     = "master"
if (-not $InstallDir) { $InstallDir = Join-Path $env:USERPROFILE "Outlook2Aula" }
$PythonVer  = "3.12.7"
$PythonUrl  = "https://www.python.org/ftp/python/$PythonVer/python-$PythonVer-amd64.exe"
$TempDir    = Join-Path $env:TEMP "O2A_install"

function Write-Step($text) {
    Write-Host ""
    Write-Host "==> $text" -ForegroundColor Cyan
}

function Update-SessionPath {
    $machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $user    = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machine;$user"
}

# -- 0. Forklar hvad scriptet goer, og bed om bekraeftelse -------------------------
$needsPython = -not (Get-Command pythonw.exe -ErrorAction SilentlyContinue)
$needsGit    = -not (Get-Command git.exe -ErrorAction SilentlyContinue)
$repoExists  = Test-Path (Join-Path $InstallDir ".git")

Write-Host "Outlook2Aula - installation" -ForegroundColor White
Write-Host ""
Write-Host "Dette script vil:"
if ($needsPython) {
    Write-Host " - Installere Python (kun for din bruger - ingen administratorrettigheder kraeves)"
}
if ($needsGit) {
    Write-Host " - Installere Git (kun for din bruger - ingen administratorrettigheder kraeves)"
}
if ($repoExists) {
    Write-Host " - Opdatere Outlook2Aula i mappen: $InstallDir"
} else {
    Write-Host " - Hente Outlook2Aula til mappen: $InstallDir"
}
if (-not $SkipShortcut) {
    Write-Host " - Oprette en genvej paa dit skrivebord"
}
if (-not $SkipLaunch) {
    Write-Host " - Starte Outlook2Aula"
}
Write-Host ""

if (-not $Force) {
    $answer = Read-Host "Vil du fortsaette? Skriv J og tryk Enter for at fortsaette, eller tryk blot Enter for at annullere"
    if ($answer.Trim().ToLower() -notin @("j", "ja", "y", "yes")) {
        Write-Host "Installation annulleret. Der er ikke aendret noget." -ForegroundColor Yellow
        exit 0
    }
}

New-Item -ItemType Directory -Force -Path $TempDir | Out-Null

# -- 1. Python ------------------------------------------------------------------
Write-Step "Tjekker Python..."
$pythonCmd = Get-Command pythonw.exe -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "Python blev ikke fundet - henter og installerer (kun for din bruger, ingen admin kraevet)..."
    $installer = Join-Path $TempDir "python-installer.exe"
    Invoke-WebRequest -Uri $PythonUrl -OutFile $installer -UseBasicParsing
    $proc = Start-Process -FilePath $installer -ArgumentList @(
        "/passive", "InstallAllUsers=0", "PrependPath=1",
        "Include_launcher=0", "Include_test=0", "Include_doc=0"
    ) -Wait -PassThru
    if ($proc.ExitCode -ne 0) { throw "Python-installationen fejlede (kode $($proc.ExitCode))." }

    Update-SessionPath
    $pyDir = Get-ChildItem "$env:LOCALAPPDATA\Programs\Python" -Directory -ErrorAction SilentlyContinue |
             Where-Object { $_.Name -like "Python3*" } |
             Sort-Object Name -Descending | Select-Object -First 1
    if (-not $pyDir) { throw "Kunne ikke finde det installerede Python bagefter." }
    $env:Path = "$($pyDir.FullName);$($pyDir.FullName)\Scripts;$env:Path"
    Write-Host "Python installeret." -ForegroundColor Green
} else {
    Write-Host "Python fundet: $($pythonCmd.Source)" -ForegroundColor Green
}
$PythonwExe = (Get-Command pythonw.exe).Source

# -- 2. Git -----------------------------------------------------------------------
Write-Step "Tjekker Git..."
$gitCmd = Get-Command git.exe -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    Write-Host "Git blev ikke fundet - henter og installerer (kun for din bruger, ingen admin kraevet)..."
    $gitInstallDir = Join-Path $env:LOCALAPPDATA "Programs\Git"
    $gitUrl = $null
    try {
        $release = Invoke-RestMethod -Uri "https://api.github.com/repos/git-for-windows/git/releases/latest" -UseBasicParsing
        $asset = $release.assets | Where-Object { $_.name -match "64-bit\.exe$" } | Select-Object -First 1
        if ($asset) { $gitUrl = $asset.browser_download_url }
    } catch {
        # Ignorer - falder tilbage til fast version nedenfor
    }
    if (-not $gitUrl) {
        $gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.46.0.windows.1/Git-2.46.0-64-bit.exe"
    }

    $installer = Join-Path $TempDir "git-installer.exe"
    Invoke-WebRequest -Uri $gitUrl -OutFile $installer -UseBasicParsing
    $dirArg = '/DIR=' + '"' + $gitInstallDir + '"'
    $proc = Start-Process -FilePath $installer -ArgumentList @(
        "/VERYSILENT", "/NORESTART", "/NOCANCEL", "/SP-", "/SUPPRESSMSGBOXES",
        $dirArg
    ) -Wait -PassThru
    if ($proc.ExitCode -ne 0) { throw "Git-installationen fejlede (kode $($proc.ExitCode))." }

    Update-SessionPath
    $env:Path = "$gitInstallDir\cmd;$env:Path"
    Write-Host "Git installeret." -ForegroundColor Green
} else {
    Write-Host "Git fundet: $($gitCmd.Source)" -ForegroundColor Green
}

# -- 3. Hent/opdater programmet ----------------------------------------------------
Write-Step "Henter Outlook2Aula..."
if (Test-Path (Join-Path $InstallDir ".git")) {
    Write-Host "Programmet findes allerede i $InstallDir - opdaterer..."
    Push-Location $InstallDir
    git fetch origin
    git reset --hard "origin/$Branch"
    Pop-Location
} elseif (Test-Path $InstallDir) {
    throw "$InstallDir findes allerede, men er ikke et git-repository. Ryd mappen eller vaelg en anden placering og proev igen."
} else {
    git clone $RepoUrl $InstallDir
}
Write-Host "Programmet er klar i $InstallDir." -ForegroundColor Green

# -- 4. Genvej paa skrivebordet ------------------------------------------------------
if (-not $SkipShortcut) {
    Write-Step "Opretter genvej paa skrivebordet..."
    try {
        $wsh = New-Object -ComObject WScript.Shell
        $shortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "Outlook2Aula.lnk"
        $shortcut = $wsh.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = Join-Path $InstallDir "updateandrun.bat"
        $shortcut.WorkingDirectory = $InstallDir
        $shortcut.Save()
        Write-Host "Genvej oprettet paa skrivebordet." -ForegroundColor Green
    } catch {
        Write-Host "Kunne ikke oprette genvej (ikke kritisk): $_" -ForegroundColor Yellow
    }
}

# -- 5. Foerste start ------------------------------------------------------------------
if (-not $SkipLaunch) {
    Write-Step "Starter Outlook2Aula..."
    Start-Process -FilePath $PythonwExe -ArgumentList "launcher.pyw" -WorkingDirectory $InstallDir
}

Write-Host ""
Write-Host "Installationen er faerdig." -ForegroundColor Green
Write-Host "Fremover starter du programmet via genvejen 'Outlook2Aula' paa skrivebordet."
if (-not $pythonCmd -or -not $gitCmd) {
    Write-Host "Bemaerk: Python og/eller Git er lige blevet installeret. Log af og paa Windows en gang," -ForegroundColor Yellow
    Write-Host "hvis genvejen ikke virker med det samme naeste gang." -ForegroundColor Yellow
}
