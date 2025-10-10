# Fixpack I — Preflight sys.path + PowerShell '||' fix (2025-09-22)

- `scripts/preflight_all.py` now bootstraps `sys.path` with project root so `import core` works even when run from scripts/.
- `scripts/release_check.ps1` uses PowerShell-native exit checks instead of Bash-style `||`.

## Apply
1) Unzip over your project.
2) Run:
   ```powershell
   python .\scripts\preflight_all.py
   ```
3) Then:
   ```powershell
   .\scripts\release_check.ps1 -ProjectRoot .
   ```
