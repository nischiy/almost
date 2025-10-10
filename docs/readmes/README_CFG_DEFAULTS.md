# CFG Defaults Patch + Self-Check Tests

## Apply cfg defaults patch
```powershell
cd G:\Bot\withouttrah
python .\scripts\patch_cfg_defaults.py
```
This injects a small normalization block after `app = ...` in `main.py` that ensures
`cfg.symbol`, `cfg.interval`, `cfg.max_bars`, `cfg.fee_bps`, `cfg.slip_bps`,
`cfg.enabled`, `cfg.paper`, `cfg.testnet` are present (from `.env` or safe defaults).

## Run the self-check test
```powershell
.\scripts\run_self_check.ps1
```
If something is still missing, the test will fail and show suggested `.env` keys.
