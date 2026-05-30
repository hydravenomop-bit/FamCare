"""
Caregivers API — list caregivers, optionally filtered by service.

GET /caregivers              → all caregivers
GET /caregivers?service_id=X → caregivers qualified for service X
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models.caregiver import Caregiver
from app.models.caregiver_service import CaregiverService


class CaregiverResponse(BaseModel):
    id: str
    name: str
    phone: Optional[str] = None

    model_config = {"from_attributes": True}


router = APIRouter()


@router.get("", response_model=list[CaregiverResponse])
async def list_caregivers(
    service_id: Optional[str] = Query(None, description="Filter by service ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    List caregivers, optionally filtered by those qualified for a specific service.
    """
    if service_id:
        query = (
            select(Caregiver)
            .join(CaregiverService, Caregiver.id == CaregiverService.caregiver_id)
            .where(CaregiverService.service_id == service_id)
            .order_by(Caregiver.name)
        )
    else:
        query = select(Caregiver).order_by(Caregiver.name)

    result = await db.execute(query)
    caregivers = result.scalars().all()
    return [CaregiverResponse.model_validate(c) for c in caregivers]
