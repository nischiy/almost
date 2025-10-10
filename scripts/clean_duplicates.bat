@echo off
REM scripts\clean_duplicates.bat
REM Windows CMD wrapper to remove duplicates (if PowerShell blocked)
SETLOCAL ENABLEDELAYEDEXPANSION

set FILES_TO_DELETE=core\strategies.py _previews

for %%F in (%FILES_TO_DELETE%) do (
  if exist "%%F" (
    echo Removing %%F ...
    rmdir /S /Q "%%F" 2>nul
    del /F /Q "%%F" 2>nul
  ) else (
    echo Skip (not found): %%F
  )
)

echo Done. Consider removing extra README_* step files if not needed.
