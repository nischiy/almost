# Refactor: order_adapter → app/services/order_adapter.py

- Переміщуємо `utils/order_adapter.py` до **app/services/order_adapter.py**.
- Патчимо всі імпорти `utils.order_adapter` → `app.services.order_adapter`.
- Тримай SRP: адаптер відповідає лише за нормалізацію payload'а ордера.

## Запуск
```powershell
cd G:\Bot\almost
powershell -ExecutionPolicy Bypass -File .\scripts\refactor\move_order_adapter.ps1 -ProjectRoot .
```
Після — прогнати тести.
