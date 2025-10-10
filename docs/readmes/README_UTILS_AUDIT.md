# Utils Audit

Скрипт робить інвентаризацію папки `utils`: використання, можливі дублі з `core/app`, наявність заглушок і дає рекомендацію.

## Запуск
```powershell
cd G:\Bot\almost
powershell -ExecutionPolicy Bypass -File .\scripts\diagnostics\run_utils_audit.ps1 -ProjectRoot .
```
Звіт: `docs/readmes/UTILS_AUDIT.md` (+ JSON).
