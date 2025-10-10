# Refactor: sender_adapter → app/services/notifications.py

- Переміщуємо `utils/sender_adapter.py` до **app/services/notifications.py** (уніфікована точка нотифікацій).
- Патчимо імпорти: `utils.sender_adapter` → `app.services.notifications` (також нормалізує `app.services.sender_adapter`).
- Роль: форматування подій (signal/fill/error/health) і доставка через канали (Telegram/Webhook/...).
- Архітектурно це **app-рівень**, ядро про канали не знає.

## Запуск
```powershell
cd G:\Bot\almost
powershell -ExecutionPolicy Bypass -File .\scripts\refactor\move_sender_adapter.ps1 -ProjectRoot .
```
Після — прогнати тести.
