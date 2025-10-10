# -*- coding: utf-8 -*-
# Runtime shim for websockets>=14 to keep legacy imports working without touching project code.
# Active ONLY when websockets version >= 14 and the new asyncio layout exists.
# Maps:
#   websockets.client  -> websockets.asyncio.client
#   websockets.server  -> websockets.asyncio.server
#   websockets.legacy.* remains untouched; prefer removing legacy imports via upgrader.
import sys
try:
    import websockets  # noqa
    from importlib import import_module
    ver = getattr(websockets, "__version__", "0")
    major = int(ver.split(".")[0]) if ver and ver[0].isdigit() else 0
    if major >= 14:
        def _alias(old_name: str, new_name: str):
            try:
                m = import_module(new_name)
                sys.modules[old_name] = m
            except Exception:
                pass  # if layout changes again, fail silently

        _alias("websockets.client", "websockets.asyncio.client")
        _alias("websockets.server", "websockets.asyncio.server")
except Exception:
    # No websockets installed or unexpected layout: do nothing
    pass
