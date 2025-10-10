# Refactor: exit_adapter → app/services/exit_adapter.py

- Переміщуємо `utils/exit_adapter.py` до **app/services/exit_adapter.py** (аплікативна логіка).
- Патчимо **усі імпорти** на `app.services.exit_adapter`.
- Якщо джерельний файл відсутній, модуль створиться з шаблону (не має знадобитися).

## Запуск
```powershell
cd G:\Bot\almost
powershell -ExecutionPolicy Bypass -File .\scripts\refactor\move_exit_adapter.ps1 -ProjectRoot .       # dry-run не потрібен, скрипт ідемпотентний
```
Після — прогнати тести.
