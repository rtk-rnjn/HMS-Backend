from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class CreateResponse(BaseModel):
    success: bool
    inserted_id: str


class UpdateResponse(BaseModel):
    success: bool
    modified_count: int
    detail: Optional[str] = None
