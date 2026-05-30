"""
Services API — list available healthcare services.

GET /services → all services with duration and pricing.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.service import Service
from app.schemas.service import ServiceResponse

router = APIRouter()


@router.get("", response_model=list[ServiceResponse])
async def list_services(db: AsyncSession = Depends(get_db)):
    """
    List all available services.

    Returns each service's name, duration (in minutes), price, and description.
    Duration is always a multiple of 15 minutes — never hardcoded.
    """
    result = await db.execute(select(Service).order_by(Service.name))
    services = result.scalars().all()
    return [ServiceResponse.model_validate(s) for s in services]
