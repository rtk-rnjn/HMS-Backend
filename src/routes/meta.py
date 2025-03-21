from __future__ import annotations

from time import perf_counter

from src.app import app, mongo_client
from src.models import PingResponse, RootResponse

__all__ = ("ping", "root")


@app.get("/ping")
async def ping() -> PingResponse:
    """
    Check if the database is reachable. Returns the response time if successful.
    """

    start = perf_counter()
    success = True
    try:
        await mongo_client.server_info()
    except Exception:
        success = False

    fin = perf_counter()

    return PingResponse(success=success, ping="pong", response_time=fin - start)


@app.get("/")
async def root() -> RootResponse:
    """
    A welcome message for the API. This endpoint is used to check if the API is running; it should always return True.
    """
    return RootResponse(success=True, message="Welcome to HMS API!")
