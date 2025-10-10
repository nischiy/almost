
# Відновлення .env

Якщо після прибирання `.env` зник — скористайся цим скриптом.

## Команди
```powershell
cd G:\Bot\almost

# Відновити .env (спершу спробує скопіювати .env.example)
powershell -ExecutionPolicy Bypass -File .\scripts\maintenance\restore_env.ps1 -ProjectRoot .
```

Примітка: якщо `.env.example` відсутній, буде створено мінімальний безпечний `.env` зі значеннями:
```
PAPER_TRADING=1
TRADE_ENABLED=0
TESTNET=0
SYMBOL=BTCUSDT
STRATEGY=ema_rsi_atr
TIMEFRAME=1m
LOG_LEVEL=INFO
BINANCE_API_KEY=
BINANCE_API_SECRET=
```
Потім заповни ключі біржі.
