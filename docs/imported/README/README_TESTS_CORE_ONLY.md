README_TESTS_CORE_ONLY.md
================================
This package replaces your test suite with a **minimal core-only** set that never hangs.

What it includes:
- pytest.ini → `testpaths = tests_core`, `norecursedirs` excludes backups like `tests_backup*`.
- tests_core/test_smoke.py → single fast test.

How to use:
1) Extract this ZIP **over** your project (you handle extraction manually).
2) Run cleanup once:  .\scripts\tests_core_only_reset.ps1
3) Run tests:         pytest -q
