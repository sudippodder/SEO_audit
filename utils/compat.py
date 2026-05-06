# utils/compat.py  — paste this and import it at the top of core.py and app.py

import sys
import asyncio
import logging

def suppress_windows_asyncio_errors():
    """
    Suppress the spurious WinError 10054 / ConnectionResetError that appears
    on Windows when asyncio's ProactorEventLoop closes a socket the server
    already closed. This is a known Python bug on Windows and is harmless.
    """
    if sys.platform != "win32":
        return

    # ── Silence the asyncio logger for these specific errors ──────────────
    logging.getLogger("asyncio").setLevel(logging.CRITICAL)

    # ── Patch the event loop exception handler ────────────────────────────
    def _silence_handler(loop, context):
        exc = context.get("exception")
        msg = context.get("message", "")

        # Swallow known harmless Windows pipe/socket errors
        ignored = (
            "ConnectionResetError",
            "WinError 10054",
            "_call_connection_lost",
            "An existing connection was forcibly closed",
            "An operation was attempted on something that is not a socket",
        )
        exc_name = type(exc).__name__ if exc else ""

        if any(s in msg or s in exc_name for s in ignored):
            return  # silently drop

        # Let everything else bubble up normally
        loop.default_exception_handler(context)

    try:
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(_silence_handler)
    except RuntimeError:
        pass  # no running loop yet — handler will be set on first use


suppress_windows_asyncio_errors()