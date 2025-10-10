# Patch v2 — fix fixtures and run.py indentation

## Apply
```powershell
python scripts\fix_failures_round3.py
pytest -s tests
```

This will:
- restore `tests/conftest.py` fixtures: `root`, `internet`, `dummy_params` (with EMA keys)
- safely comment problematic decision logging lines in `app/run.py` that caused `IndentationError`