README_CORE_TESTS.md
=====================
This package **replaces** your test suite with a minimal, fast, offline "core-only" set.

Included:
- pytest.ini  — quiet mode, maxfail=1
- tests/conftest.py — forces dry-run/offline env
- tests/test_core_smoke.py — imports core modules if present; otherwise skips

How to apply (PowerShell):
    cd G:\Bot\withouttrah
    Expand-Archive -LiteralPath .\withouttrah_tests_fresh_core_v1_XXXX.zip -DestinationPath . -Force
    # (optional) automatic replace:
    .\scripts\replace_tests_with_core.ps1 -ZipPath .\withouttrah_tests_fresh_core_v1_XXXX.zip

Run:
    pytest -q
