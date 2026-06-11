@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ENV_NAME=python_data_project_env"
set "PYTHON_VERSION=3.11"

cd /d "%~dp0.."

echo [INFO] Project directory: %CD%
echo [INFO] Searching for conda.bat...

set "CONDA_BAT="

for /f "delims=" %%I in ('where conda.bat 2^>nul') do (
    if not defined CONDA_BAT set "CONDA_BAT=%%I"
)

if not defined CONDA_BAT if exist "D:\conda\condabin\conda.bat" (
    set "CONDA_BAT=D:\conda\condabin\conda.bat"
)
if not defined CONDA_BAT if exist "%USERPROFILE%\anaconda3\condabin\conda.bat" (
    set "CONDA_BAT=%USERPROFILE%\anaconda3\condabin\conda.bat"
)
if not defined CONDA_BAT if exist "%USERPROFILE%\miniconda3\condabin\conda.bat" (
    set "CONDA_BAT=%USERPROFILE%\miniconda3\condabin\conda.bat"
)
if not defined CONDA_BAT if exist "%LOCALAPPDATA%\anaconda3\condabin\conda.bat" (
    set "CONDA_BAT=%LOCALAPPDATA%\anaconda3\condabin\conda.bat"
)
if not defined CONDA_BAT if exist "%LOCALAPPDATA%\miniconda3\condabin\conda.bat" (
    set "CONDA_BAT=%LOCALAPPDATA%\miniconda3\condabin\conda.bat"
)
if not defined CONDA_BAT if exist "%ProgramData%\anaconda3\condabin\conda.bat" (
    set "CONDA_BAT=%ProgramData%\anaconda3\condabin\conda.bat"
)
if not defined CONDA_BAT if exist "%ProgramData%\miniconda3\condabin\conda.bat" (
    set "CONDA_BAT=%ProgramData%\miniconda3\condabin\conda.bat"
)

if not defined CONDA_BAT (
    echo [ERROR] conda.bat was not found.
    exit /b 1
)

echo [INFO] Conda found: !CONDA_BAT!
call "!CONDA_BAT!" env list | findstr /R /C:"^%ENV_NAME% " >nul

if errorlevel 1 (
    echo [INFO] Creating environment %ENV_NAME%...
    call "!CONDA_BAT!" create -n "%ENV_NAME%" python="%PYTHON_VERSION%" -y
    if errorlevel 1 exit /b 1
) else (
    echo [INFO] Environment already exists.
)

call "!CONDA_BAT!" run -n "%ENV_NAME%" python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

call "!CONDA_BAT!" run -n "%ENV_NAME%" python broken_env.py
if errorlevel 1 exit /b 1

echo [OK] Environment is ready.
exit /b 0
