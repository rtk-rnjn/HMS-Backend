from __future__ import annotations

import os

from fastapi import APIRouter, Form, HTTPException
from pydantic import BaseModel

from src.app import app, database
from src.models import ADMIN_ACCESS, PATIENT_ACCESS, STAFF_ACCESS
from src.utils import Authentication

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"


class Token(BaseModel):
    access_token: str
    token_type: str


class UserLogin(BaseModel):
    email_address: str
    password: str


router = APIRouter(tags=["Login"])


@router.post("/login", response_model=Token)
async def login(email_address: str = Form(...), password: str = Form(...)):
    collection = database["users"]
    user = await collection.find_one(
        {"email_address": email_address, "password": password}
    )
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access = []
    if user["role"] == "admin":
        access = ADMIN_ACCESS
    elif user["role"] == "doctor":
        access = STAFF_ACCESS
    elif user["role"] == "patient":
        access = PATIENT_ACCESS

    token = Authentication.encode(user, *access)
    return Token(access_token=token, token_type="bearer")


app.include_router(router)
