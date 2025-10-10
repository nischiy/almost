# make_archive.ps1

Скрипт для створення чистого архіву релізу без сміття (`.venv`, `__pycache__`, `*.bak.*`, тимчасові zip-и, `*.pyc`, `*.log`).

## Використання
```powershell
cd G:\Bot\almost
powershell -ExecutionPolicy Bypass -File .\make_archive.ps1
# або з параметрами
powershell -ExecutionPolicy Bypass -File .\make_archive.ps1 -OutFile release.zip
powershell -ExecutionPolicy Bypass -File .\make_archive.ps1 -IncludeTests
powershell -ExecutionPolicy Bypass -File .\make_archive.ps1 -WhatIf   # показати, що піде в архів
```
