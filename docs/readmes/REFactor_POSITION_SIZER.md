# Refactor: position_sizer → core/positions/position_sizer.py

- Переміщуємо `utils/position_sizer.py` до **core/positions/position_sizer.py**.
- Патчимо імпорти `utils.position_sizer` → `core.positions.position_sizer`.
- Аргументація: математичне ядро sizing ближче до `core/positions` (поряд із `portfolio.py`).

## Запуск
```powershell
cd G:\Bot\almost
powershell -ExecutionPolicy Bypass -File .\scripts\refactor\move_position_sizer.ps1 -ProjectRoot .
```
Після — прогнати тести.
