
"""
Signer — HMAC-SHA256 підпис приватних запитів (Binance-compatible).
SRP: формує query + timestamp + signature; повертає headers/params.
"""
from typing import Dict, Any, Tuple
import hmac, hashlib, time, urllib.parse as _uq

def sign(params: Dict[str, Any], secret: str) -> Tuple[str, str]:
    """Повертає (query, signature)."""
    # фільтруємо None, сортуємо ключі, urlencode з safe=''
    q = "&".join(f"{_uq.quote(str(k))}={_uq.quote(str(v))}" for k, v in sorted(params.items()) if v is not None)
    sig = hmac.new(secret.encode(), q.encode(), hashlib.sha256).hexdigest()
    return q, sig

def auth_params(api_key: str, api_secret: str, extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    p = {"timestamp": int(time.time() * 1000)}
    if extra: p.update(extra)
    q, s = sign(p, api_secret)
    # Binance зазвичай вимагає signature у query; header теж корисний
    return {"query": f"{q}&signature={s}", "headers": {"X-MBX-APIKEY": api_key}}
