from __future__ import annotations

import os
from typing import Union

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from src.app import app, database
from src.models import (
    ADMIN_ACCESS,
    PATIENT_ACCESS,
    STAFF_ACCESS,
    Access,
    Admin,
    Patient,
    Staff,
)
from src.utils import Authentication

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"

ACCESS_MAP = {
    "admin": ADMIN_ACCESS,
    "doctor": STAFF_ACCESS,
    "patient": PATIENT_ACCESS,
}

ACCESS_MAP_CLASS: dict[str, BaseModel] = {
    "admin": Admin,
    "doctor": Staff,
    "patient": Patient,
}


class Token(BaseModel):
    access_token: str
    token_type: str
    user: Union[Admin, Staff, Patient]


class UserLogin(BaseModel):
    email_address: str
    password: str


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class HardPasswordChange(BaseModel):
    email_address: str
    new_password: str


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
        user=ACCESS_MAP_CLASS[user["role"]].model_validate(user),
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


async def update_password(request: Request, password_change: PasswordChange, role: str):
    collection = database["users"]
    token = request.headers.get("Authorization").split(" ")[1]
    current_user = Authentication.get_current_user(token)

    user = await collection.find_one({"email_address": current_user["sub"], "role": role})
    print(user)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    await collection.update_one(
        {"email_address": current_user["sub"], "role": role},
        {"$set": {"password": password_change.new_password}},
    )
    return {"success": True}


@router.patch("/change-password")
async def change_password(request: Request, password_change: HardPasswordChange):
    collection = database["users"]
    user = await collection.find_one({"email_address": password_change.email_address})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    await collection.update_one(
        {"email_address": password_change.email_address},
        {"$set": {"password": password_change.new_password}},
    )
    return {"success": True}


@router.patch(
    "/patient/change-password",
)
async def change_patient_password(request: Request, password_change: PasswordChange):
    return await update_password(request, password_change, role="patient")


@router.patch(
    "/admin/change-password",
)
async def change_admin_password(request: Request, password_change: PasswordChange):
    return await update_password(request, password_change, role="admin")


@router.patch(
    "/doctor/change-password",
)
async def change_doctor_password(request: Request, password_change: PasswordChange):
    return await update_password(request, password_change, role="doctor")


app.include_router(router)
