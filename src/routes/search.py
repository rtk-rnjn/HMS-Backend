from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.app import app, database
from src.models import Access, Staff
from src.utils import Authentication

router = APIRouter(tags=["Search"])


@router.get(
    "/search/doctors/name",
    dependencies=[Depends(Authentication.access_required(Access.READ_STAFF))],
)
async def search_doctor_by_name(query: str):
    collection = database["users"]
    staffs_data = await collection.find(
        {"role": "doctor", "active": True, "name": {"$regex": query, "$options": "i"}}
    ).to_list(length=100)

    return [Staff(**data) for data in staffs_data]


@router.get(
    "/search/doctors/specialization",
    dependencies=[Depends(Authentication.access_required(Access.READ_STAFF))],
)
async def search_doctor_by_specialization(query: str):
    collection = database["users"]
    staffs_data = await collection.find(
        {
            "role": "doctor",
            "active": True,
            "specialization": {"$regex": query, "$options": "i"},
        }
    ).to_list(length=100)

    return [Staff(**data) for data in staffs_data]


app.include_router(router)
