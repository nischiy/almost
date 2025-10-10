# Auto-Exits Pack v1
Purpose: bot **сам** ставить SL/TP одразу після входу.

How:
- Set policy via env:
  - Absolute: `DEFAULT_SL_PRICE`, `DEFAULT_TP_PRICE`
  - Or Percent: `DEFAULT_SL_PCT`, `DEFAULT_TP_PCT`  (e.g., 0.01 = 1%)
- Enable auto-exits:
  - `SEND_DEFAULT_EXITS=1`  **або** прапорець `-AutoExits` у go_live.ps1

Examples (LIVE):
```powershell
# 1) percent policy: 1% SL, 1% TP від ціни входу
$env:DEFAULT_SL_PCT="0.01"; $env:DEFAULT_TP_PCT="0.01"
$env:SEND_DEFAULT_EXITS="1"
$env:DRY_RUN_ONLY="0"
& .\scripts\tools\go_live.ps1 BUY MARKET

# 2) absolute policy:
$env:DEFAULT_SL_PRICE="110000"; $env:DEFAULT_TP_PRICE="120000"
$env:SEND_DEFAULT_EXITS="1"
& .\scripts\tools\go_live.ps1 BUY MARKET

# 3) або одноразово з ключем
& .\scripts\tools\go_live.ps1 BUY MARKET -AutoExits
```
Notes:
- Для percent-політики бажано мати підказку ціни входу; якщо біржа не поверне її в респонсі, можна дати `ENTRY_PRICE_HINT`.
- Використовується існуючий `exit_adapter.send_exits(...)`.
