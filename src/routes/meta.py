from __future__ import annotations

import binascii
import hashlib
import hmac
import os
from time import perf_counter

from fastapi import Header, HTTPException
from pydantic import BaseModel

from src.app import app, mongo_client
from src.models import PingResponse, RootResponse

__all__ = ("ping", "root")

GITHUB_SECRET = os.environ["GITHUB_WEBHOOK_SECRET"]


class GitHubPushPayload(BaseModel):
    ref: str


def verify_signature(x_hub_signature_256: str = Header(...), body: bytes = b""):
    digest = hmac.new(GITHUB_SECRET.encode(), body, hashlib.sha256).digest()
    expected_signature = "sha256=" + binascii.hexlify(digest).decode()

    if not hmac.compare_digest(expected_signature, x_hub_signature_256):
        raise HTTPException(status_code=403, detail="Invalid signature")


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
