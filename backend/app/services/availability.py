"""
Slot Availability Service.

Computes available time slots for a service on a given date.
Slots are 15-minute aligned and duration-aware — a 60-min service
at 10:00 blocks 10:00, 10:15, 10:30, 10:45 as start times.

The core overlap check:
    overlap = (new_start < existing_end) AND (existing_start < new_end)
"""

from datetime import time, timedelta, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.service import Service
from app.models.caregiver import Caregiver
from app.models.caregiver_service import CaregiverService
from app.models.booking import BookingItem, Booking
from app.schemas.slot import (
    SlotResponse,
    SlotAvailabilityResponse,
    AvailableCaregiver,
)


settings = get_settings()


def _time_to_minutes(t: str) -> int:
    """Convert 'HH:MM' string to minutes since midnight."""
    h, m = map(int, t.split(":"))
    return h * 60 + m


def _minutes_to_time(minutes: int) -> str:
    """Convert minutes since midnight to 'HH:MM' string."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _generate_candidate_starts(duration_minutes: int) -> list[int]:
    """
    Generate all valid 15-min-aligned start times (in minutes since midnight)
    such that the full service duration fits within business hours.

    Example: duration=60, hours 8-20
    → starts from 480 (8:00) to 1140 (19:00), step 15
    """
    start_min = settings.SLOT_START_HOUR * 60
    end_min = settings.SLOT_END_HOUR * 60
    granularity = settings.SLOT_GRANULARITY_MINUTES

    candidates = []
    t = start_min
    while t + duration_minutes <= end_min:
        candidates.append(t)
        t += granularity
    return candidates


def _has_overlap(
    new_start: int, new_duration: int,
    existing_start: int, existing_duration: int,
) -> bool:
    """
    Check if two time ranges overlap.

    Overlap formula:
        new_start < existing_start + existing_duration
        AND existing_start < new_start + new_duration

    This correctly handles:
    - Partial overlaps
    - Full containment
    - Adjacent slots (10:00-11:00 and 11:00-11:30 → NO overlap)
    """
    new_end = new_start + new_duration
    existing_end = existing_start + existing_duration
    return new_start < existing_end and existing_start < new_end


async def get_available_slots(
    db: AsyncSession,
    service_id: str,
    date: str,
) -> SlotAvailabilityResponse:
    """
    Compute available slots for a service on a given date.

    Algorithm:
    1. Fetch service → get duration_minutes
    2. Find all caregivers qualified for this service
    3. For each caregiver, fetch their existing bookings on that date
    4. For each candidate time slot, check if the caregiver is free
       (no overlap with any existing booking, using full duration)
    5. Return slots grouped by time with available caregivers

    Raises ValueError if service_id is not found.
    """
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()
    if service is None:
        raise ValueError(f"Service with id '{service_id}' not found")

    duration = service.duration_minutes

    cg_query = (
        select(Caregiver)
        .join(CaregiverService, Caregiver.id == CaregiverService.caregiver_id)
        .where(CaregiverService.service_id == service_id)
    )
    cg_result = await db.execute(cg_query)
    caregivers = list(cg_result.scalars().all())

    if not caregivers:
        return SlotAvailabilityResponse(
            service_id=service_id,
            service_name=service.name,
            duration_minutes=duration,
            date=date,
            slots=[],
        )

    caregiver_ids = [cg.id for cg in caregivers]
    bookings_query = (
        select(BookingItem)
        .join(Booking, BookingItem.booking_id == Booking.id)
        .where(
            BookingItem.caregiver_id.in_(caregiver_ids),
            BookingItem.slot_date == date,
            Booking.status == "confirmed",
        )
    )
    bookings_result = await db.execute(bookings_query)
    existing_bookings = list(bookings_result.scalars().all())

    cg_bookings: dict[str, list[BookingItem]] = {cg.id: [] for cg in caregivers}
    for bi in existing_bookings:
        if bi.caregiver_id in cg_bookings:
            cg_bookings[bi.caregiver_id].append(bi)

    candidates = _generate_candidate_starts(duration)

    slots: list[SlotResponse] = []
    for start_minutes in candidates:
        available_cgs: list[AvailableCaregiver] = []

        for cg in caregivers:
            is_free = True
            for bi in cg_bookings[cg.id]:
                existing_start = _time_to_minutes(bi.start_time)
                if _has_overlap(start_minutes, duration, existing_start, bi.duration_minutes):
                    is_free = False
                    break

            if is_free:
                available_cgs.append(AvailableCaregiver(id=cg.id, name=cg.name))

        if available_cgs:
            slots.append(
                SlotResponse(
                    start_time=_minutes_to_time(start_minutes),
                    end_time=_minutes_to_time(start_minutes + duration),
                    available_caregivers=available_cgs,
                )
            )

    return SlotAvailabilityResponse(
        service_id=service_id,
        service_name=service.name,
        duration_minutes=duration,
        date=date,
        slots=slots,
    )
