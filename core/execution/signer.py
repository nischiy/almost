# utils/signer.py
from __future__ import annotations
import hmac, hashlib, time, urllib.parse as up

def timestamp_ms() -> int:
    return int(time.time() * 1000)

def sign_query(secret: str, params: dict) -> str:
    """
    Returns query string with signature appended as 'signature='.
    """
    qs = up.urlencode(params, doseq=True)
    sig = hmac.new(secret.encode('utf-8'), qs.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"{qs}&signature={sig}"
