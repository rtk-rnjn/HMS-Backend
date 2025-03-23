from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Union
from src.app import app, database
from src.models import ADMIN_ACCESS, PATIENT_ACCESS, STAFF_ACCESS, Admin, Staff, Patient
from src.utils import Authentication

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"

ACCESS_MAP = {
    "admin": ADMIN_ACCESS,
    "doctor": STAFF_ACCESS,
    "patient": PATIENT_ACCESS,
}

ACCESS_MAP_CLASS: dict[str: BaseModel] = {
    "admin": Admin,
    "doctor": Staff,
    "patient": Patient
}


class Token(BaseModel):
    access_token: str
    token_type: str
    user: Union[Admin, Staff, Patient]


class UserLogin(BaseModel):
    email_address: str
    password: str


router = APIRouter(tags=["Login"])


async def authenticate_user(email_address: str, password: str, role: str | None = None):
    query = {"email_address": email_address, "password": password}
    if role:
        query["role"] = role

    user = await database["users"].find_one(query)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return Token(
        access_token=Authentication.encode(user, *ACCESS_MAP[user["role"]]),
        token_type="bearer",
        user=ACCESS_MAP_CLASS[user["role"]].model_validate(user)
    )


@router.post("/admin/login", response_model=Token)
async def admin_login(user: UserLogin):
    return await authenticate_user(user.email_address, user.password, "admin")


@router.post("/doctor/login", response_model=Token)
async def doctor_login(user: UserLogin):
    return await authenticate_user(user.email_address, user.password, "doctor")


@router.post("/patient/login", response_model=Token)
async def patient_login(user: UserLogin):
    return await authenticate_user(user.email_address, user.password, "patient")


app.include_router(router)
