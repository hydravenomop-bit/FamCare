"""
Slots API — get available time slots for a service on a date.

GET /slots/available?service_id=<uuid>&date=<YYYY-MM-DD>

Returns 15-min-aligned time slots with available caregivers for each slot.
Slots are duration-aware — a 60-min service shows slots where the full
duration fits within business hours and doesn't overlap existing bookings.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.slot import SlotAvailabilityResponse
from app.services.availability import get_available_slots

router = APIRouter()


@router.get("/available", response_model=SlotAvailabilityResponse)
async def available_slots(
    service_id: str = Query(..., description="Service UUID"),
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get available time slots for a service on a specific date.

    Returns slots with available caregivers. A slot is available for a
    caregiver if the caregiver has no overlapping bookings (checked using
    full service duration, not just start time).

    Slots are 15-minute aligned and only returned where the full service
    duration fits within business hours.
    """
    try:
        result = await get_available_slots(db, service_id, date)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
