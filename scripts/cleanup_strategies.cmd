@echo off
setlocal
set PS=powershell -ExecutionPolicy Bypass -NoLogo -NoProfile
%PS% -File "%~dp0cleanup_strategies.ps1" -ProjectRoot "%cd%" -Keep ema_rsi_atr.py
endlocal
