@echo off
REM Run from project root
python scripts\fix_run_future_order.py
if %ERRORLEVEL% NEQ 0 (
    echo Failed to fix file order. See message above.
    exit /b 1
)
echo Done.
