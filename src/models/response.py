from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class CreateResponse(BaseModel):
    success: bool
    inserted_id: str


class UpdateResponse(BaseModel):
    success: bool
    modified_count: int
    detail: Optional[str] = None


class PingResponse(BaseModel):
    success: bool = Field(
        ...,
        description="Whether the ping was successful. True if database is reachable, False otherwise.",
    )
    ping: Literal["pong"] = Field(
        "pong",
        description="The response to the ping request. Should be 'pong' if successful.",
    )
    response_time: float = Field(
        ...,
        description="The time taken to receive a response from the database in seconds.",
    )


class RootResponse(BaseModel):
    success: Literal[True] = Field(
        True,
        description="Whether the request was successful. Should always be True.",
        frozen=True,
    )
    message: Literal["Welcome to HMS API!"] = Field(
        "Welcome to HMS API!",
        description="A welcome message for the API.",
        frozen=True,
    )


class BaseResponse(BaseModel):
    success: bool
