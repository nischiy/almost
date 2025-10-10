# Safety Playbook (Optional, Non-Invasive)

- **Circuit Breaker (`core/circuit_breaker.py`)**: prevents cascaded failures in live by blocking new actions
  when the sentinel file `circuit.open` exists or when too many consecutive failures happen.
- **Feature Flags (`core/feature_flags.py`)**: toggle behaviors via environment variables or `.flags.json` without redeploy.

## Quick use
```python
from core.circuit_breaker import CircuitBreaker
br = CircuitBreaker(consecutive_failures_threshold=3, open_cooldown_sec=30)
if br.allow():
    ok = True  # place your order here
    br.report(ok)
else:
    print("Circuit open — skipping")
```
Sentinel stop:
```
# PowerShell
ni circuit.open -ItemType File | Out-Null   # stop
rm circuit.open                             # resume
```

File flags:
```json
{ "DRY_MODE": "on", "USE_NEW_RISK": true }
```
