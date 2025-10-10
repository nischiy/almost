
PROD Step 1/8 — Precision & Symbol Filters (Binance Futures)

Що всередині
------------
* scripts/prod_step1_precision.py — ідемпотентний патчер. Додає в core/execution/binance_futures.py
  утиліти:
    - get_exchange_info (кеш)
    - get_symbol_filters (LOT_SIZE / PRICE_FILTER / MIN_NOTIONAL)
    - round_qty_price
    - validate_min_notional
    - prepare_order_for_symbol(...)

Важливо
-------
• НІЧОГО не ламає і не змінює існуючі виклики створення ордерів — тільки додає інфраструктуру.
• Інтеграцію в app/run.py зробимо окремим кроком (Step 2).

Як застосувати
--------------
1) Розпакуйте архів у корінь репо (файл стане   scripts/prod_step1_precision.py).
2) Запустіть:
     python .\scripts\prod_step1_precision.py

Очікування
----------
Побачите:
    [OK] Patched: core\execution\binance_futures.py
    [OK] Backup:  core\execution\binance_futures.py.bak_step1_YYYYMMDD_HHMMSS
    [NOTE] Added symbol filters, rounding and minNotional validation utilities.

Перевірка (опціонально)
-----------------------
У REPL:
    from core.execution.binance_futures import prepare_order_for_symbol
    import requests
    sess = requests.Session()
    res = prepare_order_for_symbol(sess, "https://fapi.binance.com", "BTCUSDT", "BUY",
                                   notional_usdt=20, last_price=115000.0)
    print(res)

Якщо ок — переходимо до Step 2 (інтеграція у app/run.py).
