from __future__ import annotations

import os
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

if TYPE_CHECKING:
    from type import Client
else:
    from razorpay import Client as Client


load_dotenv()

URI = os.getenv("MONGODB_URI")

if URI is None:
    raise ValueError("MONGODB_URI is not set")

mongo_client = AsyncIOMotorClient(URI, document_class=dict)
database = mongo_client["HMS"]

RAZORPAY_KEY = os.getenv("RAZORPAY_KEY")
RAZORPAY_SECRET = os.getenv("RAZORPAY_SECRET")

razorpay_client = Client(auth=(RAZORPAY_KEY, RAZORPAY_SECRET))
razorpay_client.set_app_details(
    {"title": "Hospital Management System", "version": "Initial 0.1"}
)


app = FastAPI(
    title="HMS API Documentation",
    version="0.1",
    contact={
        "name": "Team 06 @ Infosys",
        "url": "https://github.com/rtk-rnjn/HMS-Backend",
    },
    license_info={
        "name": "Mozilla Public License Version 2.0",
        "url": "https://opensource.org/licenses/MPL-2.0",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],
)

from .routes import *  # noqa: E402, F401, F403
