@echo off
setlocal

set ENV_NAME=python_data_project_env
set PYTHON_VERSION=3.11

echo [INFO] Checking conda...

where conda >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Conda not found.
    exit /b 1
)

echo [INFO] Conda found.

echo [INFO] Checking environment %ENV_NAME%...

call conda env list | findstr /C:"%ENV_NAME%" >nul

if errorlevel 1 (
    echo [INFO] Environment not found. Creating environment...

    call conda create -n %ENV_NAME% python=%PYTHON_VERSION% -y

    if errorlevel 1 (
        echo [ERROR] Failed to create environment.
        exit /b 1
    )
) else (
    echo [INFO] Environment already exists.
)

echo [INFO] Installing requirements...

call conda run -n %ENV_NAME% python -m pip install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] Failed to install requirements.
    exit /b 1
)

echo [INFO] Running smoke test...

call conda run -n %ENV_NAME% python broken_env.py

if errorlevel 1 (
    echo [ERROR] Smoke test failed.
    exit /b 1
)

echo [OK] Environment is ready.

exit /b 0