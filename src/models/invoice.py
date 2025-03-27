from __future__ import annotations

from pydantic import BaseModel, Field


class Invoice(BaseModel):
    id: str = Field(..., alias="_id")
    appointment_id: str
    razorpay_payment_id: str
