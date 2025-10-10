param(
  [string]$ProjectRoot = "."
)
$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$py = Join-Path -Path $root -ChildPath ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $py)) { $py = "python" }

# Create a temporary Python script
$tmp = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "diag_binance_{0}.py" -f ([guid]::NewGuid().ToString("N")))
@'
import sys, pkgutil, importlib
print("=== Python interpreter:", sys.executable)
try:
    m = importlib.import_module("binance")
    print("binance module file:", getattr(m, "__file__", "<?>"))
    try:
        names = [mod.name for mod in pkgutil.iter_modules(m.__path__)]
    except Exception:
        names = []
    print("binance package contents (top level):", sorted(names))
    try:
        from binance import __version__ as v2
        print("binance.__version__:", v2)
    except Exception:
        pass
    try:
        import binance.um_futures as um
        print("um_futures FOUND at:", getattr(um, "__file__", "<?>"))
    except Exception as e:
        print("um_futures import error:", type(e).__name__, e)
except Exception as e:
    print("FAILED to import top-level 'binance':", type(e).__name__, e)
'@ | Out-File -LiteralPath $tmp -Encoding UTF8

& $py $tmp
Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
