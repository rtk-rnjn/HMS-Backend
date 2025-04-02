from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.app import app

router = APIRouter(tags=["Razorpay"])
from fastapi.responses import JSONResponse
