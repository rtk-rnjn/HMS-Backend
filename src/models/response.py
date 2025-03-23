from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class PingResponse(BaseModel):
    success: Literal[True] = True
    ping: Literal["pong"] = "pong"
    response_time: float


class RootResponse(BaseModel):
    success: Literal[True] = True
    message: Literal["Welcome to HMS API!"] = "Welcome to HMS API!"
