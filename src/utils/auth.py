from __future__ import annotations

import datetime
import os

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from src.models import Access

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


class Authentication:
    @staticmethod
    def encode(data: dict, *access: Access) -> str:
        future_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            days=1
        )

        encodable = {}
        encodable["exp"] = future_date
        encodable["access"] = [a.value for a in access]
        encodable["role"] = data["role"]
        encodable["sub"] = str(data["email_address"])
        encodable["_id"] = str(data["_id"])

        return jwt.encode(encodable, SECRET_KEY, ALGORITHM)

    @staticmethod
    def decode(token: str) -> dict:
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except Exception:
            return {}

    @staticmethod
    def get_current_user(token: str = Depends(oauth2_scheme)):
        payload = Authentication.decode(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload

    @staticmethod
    def access_required(*access: Access):
        def dependency(current_user: dict = Depends(Authentication.get_current_user)):
            user_access = current_user["access"]
            for a in access:
                if a.value not in user_access:
                    raise HTTPException(status_code=403, detail="Access denied")

        return dependency
