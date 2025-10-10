# Surprise Tools (drop-in)
Це набір **безпечних**, окремих PowerShell-утиліт. Вони нічого не ламають і не змінюють код ядра.

## Що всередині
- `scripts/tools/tradewatch.ps1` — міні-дашборд: тікер, спред, режим (mainnet/testnet), баланси, останній бек‑тест.
- `scripts/tools/panic_switch.ps1` — миттєво ставить `TRADE_ENABLED=0` у `.env` (робить бекап).
- `scripts/tools/enable_trading_safe.ps1` — вмикає `TRADE_ENABLED=1` з елементарними перевірками ризиків (`-Force`, `-TestnetOnly`).
- `scripts/maintenance/log_rotate.ps1` — архівація старих логів (за замовчуванням старше 7 днів).
- `scripts/tools/health.ps1` — міні-«все ок?» (preflight → smoke → paper report).

## Встановлення
1. Розпакуй **в корінь репозиторію** (поряд з `scripts`, `logs`, `.env`). Шляхи збережені.
2. Запусти:
   - `.\scripts\tools\tradewatch.ps1`
   - `.\scripts\tools\panic_switch.ps1`
   - `.\scripts\tools\enable_trading_safe.ps1 -TestnetOnly` (або `-Force`)
   - `.\scripts\maintenance\log_rotate.ps1 -Days 10`
   - `.\scripts\tools\health.ps1 -Strict`

**Нічого з цього не потребує зміни існуючих файлів (окрім .env для перемикачів).**
