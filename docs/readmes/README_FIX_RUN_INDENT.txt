= Fix unexpected indent in app/run.py (tests) =

1) Unzip into your project root so that you have:
   scripts\fix_run_indent_and_tests.py

2) Run:
   python scripts\fix_run_indent_and_tests.py

   - The script makes a timestamped backup of app\run.py
   - Rebuilds the problematic try/except block that logs "Klines load failed: %s"
   - Verifies syntax via AST

3) Then run tests:
   pytest -s tests