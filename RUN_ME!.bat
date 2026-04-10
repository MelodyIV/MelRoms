@echo off
setlocal enabledelayedexpansion
title MelRoms // Launcher Installer
color 0b

echo.
echo  *********************************************************
echo  * *
echo  * Welcome to the MelRoms Installer           *
echo  * *
echo  *********************************************************
echo.
echo  This script will prepare your Windows 
echo  environment for the MelRoms suite.
echo.
powershell -Command "Write-Host ' [!] IMPORTANT NOTICE [!] ' -ForegroundColor Yellow -BackgroundColor Black"
echo.
echo  This software is NOT malicious. However, please note:
echo  1. Significant portions of this suite were AI-generated.
echo  2. While the creator has experienced 100%% stability, 
echo     AI code can occasionally contain unexpected bugs.
echo  3. These bugs could potentially affect or corrupt data.
echo.
echo  By proceeding, you acknowledge that you are using this 
echo  software at your own risk.
echo.

:validation
set /p "user_input=Please type 'i understand' to proceed: "
if /I "!user_input!"=="i understand" (
    cls
    goto start_install
) else (
    echo.
    powershell -Command "Write-Host ' Invalid input. Please type the phrase exactly to continue. ' -ForegroundColor White -BackgroundColor DarkRed"
    echo.
    goto validation
)

:start_install
echo.
powershell -Command "Write-Host ' [SYSTEM INITIALIZATION] ' -ForegroundColor Cyan"
echo  ---------------------------------------------------------
echo  Building environment...
echo.

:: Check for Admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    powershell -Command "Write-Host ' [ERROR] Please run this script as ADMINISTRATOR. ' -ForegroundColor White -BackgroundColor DarkRed"
    pause
    exit /b
)

:: Install MSVC Redistributable
echo [+] Preparing MSVC Redistributable (x64)...
set "vcredist_url=https://aka.ms/vs/17/release/vc_redist.x64.exe"
set "vcredist_file=%TEMP%\vcredist_x64.exe"
powershell -Command "Invoke-WebRequest -Uri '%vcredist_url%' -OutFile '%vcredist_file%'"
if exist "%vcredist_file%" (
    echo [ACTION] Please follow the prompts in the installer window...
    start /wait "" "%vcredist_file%" /passive
    del "%vcredist_file%"
) else (
    echo [WARNING] Could not download VC Redist.
)

:: Install Python if missing
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [+] Python not found. Deploying Python 3.12...
    set "py_url=https://www.python.org/ftp/python/3.12.2/python-3.12.2-amd64.exe"
    set "py_file=%TEMP%\python_installer.exe"
    powershell -Command "Invoke-WebRequest -Uri '%py_url%' -OutFile '%py_file%'"
    if exist "!py_file!" (
        echo [ACTION] Opening Python Installer... 
        echo [!] REMEMBER TO CHECK 'ADD TO PATH' [!]
        start /wait "" "!py_file!"
        del "!py_file!"
        call :RefreshEnv
    ) else (
        echo [ERROR] Failed to download Python installer.
        pause
        exit /b
    )
)

:: Install Dependencies
echo [+] Updating Pip...
python -m pip install --upgrade pip

echo [+] Installing module dependencies...
:: Installing in smaller chunks to prevent massive hang-ups
python -m pip install pygame-ce psutil pygetwindow ping3 GPUtil pycryptodome
python -m pip install yt-dlp python-vlc Pillow mutagen pyautogui pynput
python -m pip install pydivert pypresence ollama customtkinter pyttsx3 
python -m pip install requests pygments discord.py

:: Fetch WinDivert
echo [+] Fetching WinDivert Binary Kernel...
set "wd_url=https://github.com/basil00/WinDivert/releases/download/v2.2.2/WinDivert-2.2.2-A.zip"
set "wd_zip=%TEMP%\windivert.zip"
set "wd_extract=%TEMP%\wd_tmp"
powershell -Command "Invoke-WebRequest -Uri '%wd_url%' -OutFile '%wd_zip%'"
if exist "%wd_zip%" (
    powershell -Command "Expand-Archive -Path '%wd_zip%' -DestinationPath '%wd_extract%' -Force"
    copy /y "%wd_extract%\WinDivert-2.2.2-A\x64\WinDivert.dll" . >nul
    copy /y "%wd_extract%\WinDivert-2.2.2-A\x64\WinDivert64.sys" . >nul
    rd /s /q "%wd_extract%"
    del "%wd_zip%"
) else (
    echo [WARNING] Could not download WinDivert binaries.
)

echo.
echo  ---------------------------------------------------------
powershell -Command "Write-Host ' [SUCCESS] Setup Complete! ' -ForegroundColor Green"
echo  Launch MelRoms_Launcher.pyw to begin.
echo  ---------------------------------------------------------
echo.
pause
exit /b

:RefreshEnv
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "SysPath=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "UserPath=%%b"
set "PATH=%SysPath%;%UserPath%;%PATH%"
goto :EOF