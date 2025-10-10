@echo off
REM Run the PowerShell script make_archive.ps1 from the same folder
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0make_archive.ps1"
pause
