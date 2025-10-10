Paper offline runner (ASCII-only)
-----------------------------------
What it does:
1) Runs preflight in Strict mode
2) Runs pytest -q -vv
3) Calls your existing smoke pipeline
4) Copies smoke last.json into logs/paper/last.json

How to use:
- Extract this ZIP into the repo root so that scripts/paper/*.ps1 appear.
- In an activated venv, from the repo root run:
  .\scripts\paper\run_paper.ps1

- To view the last paper report:
  .\scripts\paper\show_last.ps1

Notes:
- No non-ASCII characters to avoid codepage issues.
- Does not modify your project code or tests.
