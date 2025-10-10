$ErrorActionPreference = "Stop"
$py = ".\.venv\Scripts\python.exe"

Write-Host ">>> Installing pytest (if needed)"
.\.venv\Scripts\pip.exe install -U pytest | Out-Null

Write-Host ">>> Project Imports & Syntax Verification"
& $py -m pytest -q tests\test_project_imports.py --junitxml=logs\pytest_imports.xml

Write-Host ">>> CLI Scripts Smoke"
& $py -m pytest -q tests\test_scripts_cli.py --junitxml=logs\pytest_scripts.xml

Write-Host ">>> End-to-End Pipeline"
& $py -m pytest -q tests\test_pipeline_end_to_end.py --junitxml=logs\pytest_pipeline.xml

Write-Host ">>> All checks done. Reports in logs\\pytest_*.xml"
