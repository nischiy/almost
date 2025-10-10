
# Backtest Pack (6 months, live-like)

Це автономний бектест твоєї EMA/RSI/ATR-логіки з фільтрами/ризиком, максимально наближений до live:
- 1m дані з Binance USDT-M Futures (через `python-binance`).
- Комісії (за замовчуванням 0.02% такер **на кожну сторону**) та ковзання (1 bps на сторону).
- SL/TP по **ATR**; детект спрацювань по **high/low**.
- Гейти: **сесія, ATR-percentile, HTF-EMA-тренд** (увімкнені за замовчуванням).
- RiskManager: ліміти на кількість угод/денної втрати/послідовні збитки/розмір позиції.

## Запуск (пів року BTCUSDT, 1m)
```powershell
.\.venv\Scripts\python.exe scripts\backtest.py --symbol BTCUSDT --interval 1m --months 6 --leverage 5 --position-usd 50
```

> Хочеш використати свої параметри: поклади їх у `models/ema_rsi_atr/best_params.json` або передай `--params path\to\best_params.json`.

## Опції
- `--start YYYY-MM-DD --end YYYY-MM-DD` — фіксований діапазон (UTC).
- `--fee-bps 2.0` — такер комісія на сторону (біпси).
- `--slippage-bps 1.0` — ковзання на сторону (біпси).
- `--no-gates` — вимкнути стратегеїчні фільтри (не рекомендовано).
- `--session-hours 7-22` — активні години (UTC).
- `--weekdays 1-5` — активні дні (1..5 = будні).
- `--atr-pct 10,90,200` — p_low,p_high,lookback для ATR-процентиля.
- `--htf trend,ema_slow,20` — режим/колонка/довжина для тренд-фільтра.
- `--csv path.csv` — замість Binance API взяти локальний CSV (`open_time,open,high,low,close,volume`).

## Виходи
Створиться папка `logs/backtest/<timestamp>/` з:
- `trades.csv` — усі угоди;
- `equity.csv` — крива еквіті;
- `config.json` — фактичні параметри;
- `report.md` — короткий підсумок (PnL, win-rate, expectancy, DD, Sharpe proxy).

## Нотатки
- Параметри за замовчуванням обрані консервативно. Щоб “в історії вийшов профіт”, щонайменше **не вимикай гейти** і використовуй **адекватні `tp_atr_mult/sl_atr_mult`** (напр., `2.0/1.0`) та **помірні комісії/ковзання**.
- Я не обіцяю прибуток у майбутньому; цей бектест дає “X-ray” твоєї поточної логіки на історії з урахуванням біржових витрат.
