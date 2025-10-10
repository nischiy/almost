$ErrorActionPreference = "Stop"
$py = ".\.venv\Scripts\python.exe"
Write-Host ">>> Installing pytest (if needed)"
.\.venv\Scripts\pip.exe install -U pytest | Out-Null
Write-Host ">>> Running tests"
& $py -m pytest -q --junitxml=logs\pytest_report.xml
Write-Host ">>> Report saved to logs\pytest_report.xml"
