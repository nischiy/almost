\
    @echo off
    REM Fallback: run the Python helper to print clickable file:/// URIs
    setlocal
    set SCRIPT=%~dp0print_last_trading_links.py
    if exist "%SCRIPT%" (
        "%~dp0..\..\.venv\Scripts\python.exe" "%SCRIPT%" 2>nul || python "%SCRIPT%"
    ) else (
        echo Python helper not found: %SCRIPT%
    )
    endlocal
