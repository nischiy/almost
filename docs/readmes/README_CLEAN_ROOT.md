
# Clean root (allowlist)

## Мета
Тримати корінь репозиторію чистим: залишити тільки базові файли запуску та релізу.

**Залишає в корені:**
- `main.py`
- `.env` / `.env.example`
- `requirements.txt` / `requirements.append.txt`
- `make_archive.ps1` / `make_archive.bat`

Інші файли:
- README/PATCH/NOTES переносяться в `docs/readmes/`.
- решта **видаляється** (тільки файли в корені; директорії не чіпаються).

## Запуск
```powershell
cd G:\Bot\almost

# Сухий прогон
powershell -ExecutionPolicy Bypass -File .\scripts\maintenance\clean_root_allowlist.ps1 -ProjectRoot . -WhatIf

# Фактичне прибирання
powershell -ExecutionPolicy Bypass -File .\scripts\maintenance\clean_root_allowlist.ps1 -ProjectRoot .
```
