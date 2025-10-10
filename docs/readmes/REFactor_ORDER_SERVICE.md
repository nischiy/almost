# Refactor: order_service → app/services/order_service.py

- Переміщуємо `utils/order_service.py` до **app/services/order_service.py**.
- Патчимо імпорти `utils.order_service` → `app.services.order_service`.
- Призначення: інфраструктурний шар поверх ExecutorService (ретраї, rate-limit, dry-run, логування).

## Запуск
```powershell
cd G:\Bot\almost
powershell -ExecutionPolicy Bypass -File .\scripts\refactor\move_order_service.ps1 -ProjectRoot .
```
Далі — прогнати тести.
