
This patch replaces main.py with a normalization shim so that both UPPER/lowercase .env keys are supported.
It also derives base_url from BINANCE_TESTNET when missing.
