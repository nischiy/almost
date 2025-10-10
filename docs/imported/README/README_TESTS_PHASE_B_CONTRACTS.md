README_TESTS_PHASE_B_CONTRACTS.md
=======================================
Phase B = **контрактні тести**. Вони **НЕ** скіпаються — якщо ключового модуля нема, буде **FAIL із точним повідомленням**, що саме треба додати.

Що перевіряємо обовʼязково:
- backtest: існує `core.backtest` або `backtest.py` з функціями `backtest_ema_rsi_atr`/`backtest_ema_rsi`/`run_backtest`.
- risk: існує `core.risk` або `risk.py` з `RiskManager` або `check_limits`.
- utils: існує `utils.py` і імпортується.
- telemetry: існує `core.telemetry.save_snapshot(...)`.

Запуск:
    pytest -q -vv

Мета:
- Мінімізувати "скіпи" і дати чіткі **точки поломки** з інструкцією, що додати в проєкт.
