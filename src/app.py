from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

URI = os.getenv("MONGODB_URI")

if URI is None:
    raise ValueError("MONGODB_URI is not set")

mongo_client = AsyncIOMotorClient(URI, document_class=dict)
database = mongo_client["HMS"]

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

from .routes import *  # noqa: E402, F401, F403
