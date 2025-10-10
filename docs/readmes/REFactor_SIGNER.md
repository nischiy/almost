# Refactor: signer → core/execution/signer.py

- Переміщуємо `utils/signer.py` до **core/execution/signer.py**.
- Патчимо імпорти `utils.signer` → `core.execution.signer`.
- Причина: підпис — це **біржовий/execution шар**, тісно пов'язаний з транспортом приватних запитів.

## Запуск
```powershell
cd G:\Bot\almost
powershell -ExecutionPolicy Bypass -File .\scripts\refactor\move_signer.ps1 -ProjectRoot .
```
Після — прогнати тести. Якщо потрібна ін'єкція (DIP), імпортуй як абстрактний "Signer".
