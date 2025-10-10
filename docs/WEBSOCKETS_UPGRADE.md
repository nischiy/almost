# WebSockets (package: websockets) - dependency policy

Current policy: `websockets>=14,<16` (major 14/15).

The project does not use deprecated imports (`websockets.client/server/legacy`), so no shims are required.
If a third-party package expects the old API, use the official paths `websockets.asyncio.client/server`
or check that package documentation.

## Install
```powershell
pip install "websockets>=14,<16"
```

## Note
If you temporarily need to downgrade, use the legacy mode via `constraints.txt`.
