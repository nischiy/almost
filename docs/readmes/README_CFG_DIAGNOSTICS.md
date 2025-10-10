# CFG Diagnostics & Self-Check

This bundle helps you quickly **see all missing `cfg.*` attributes** that your code expects,
so you can update `.env` or your config builder once — instead of fixing them one-by-one at runtime.

## How to use

1. Unzip into your project root (so paths like `scripts/diagnostics/scan_cfg_attrs.py` exist).
2. Run the self-check (PowerShell):
   ```powershell
   cd G:\Bot\withouttrah
   .\.venv\Scripts\activate
   python -m pip install pytest -q
   .\scripts\run_self_check.ps1
   ```
3. Open `logs/self_check_cfg_attrs.txt` or read the terminal output.
   If there are missing attributes, the test will **fail** and print suggested `.env` keys to set (e.g. `MAX_BARS`).
4. Add the keys to your `.env`, re-run the self-check until it passes.
