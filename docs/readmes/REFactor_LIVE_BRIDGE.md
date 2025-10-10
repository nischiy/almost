# Refactor: live_bridge → app/services/bridge.py

- Переміщуємо `utils/live_bridge.py` до **app/services/bridge.py**.
- Патчимо всі імпорти `utils.live_bridge` → `app.services.bridge`.
- Це шар **оркестрації** (fetch → decide → execute) на рівні застосунку.

## Запуск
```powershell
cd G:\Bot\almost
powershell -ExecutionPolicy Bypass -File .\scripts\refactor\move_live_bridge.ps1 -ProjectRoot .
```
Після — прогнати тести.
