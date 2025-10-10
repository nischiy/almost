# Fixpack G — entrypoint logging bootstrap (2025-09-22)

- Replaces `app/entrypoint.py` with a version that sets up logging (if none), prints start/finish banners,
  and remains cfg/signature-aware.
- Adds `scripts/diagnose_entry.py` to quickly inspect `TraderApp` constructor and available runner methods.

## Apply
1) Unzip over your project.
2) Run paper:
   ```powershell
   .\scripts\run_paper.ps1 -ProjectRoot . -Symbol BTCUSDT -Interval 1m
   ```
3) If you still see no output, run diagnostics:
   ```powershell
   python .\scripts\diagnose_entry.py
   ```
