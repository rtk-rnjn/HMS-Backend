from __future__ import annotations

import asyncio
import os

from src.app import app

if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
else:
    try:
        import uvloop

        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except ImportError:
        pass

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8080))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT, log_level="debug")
