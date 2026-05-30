"""
Atomic Checkout Service.

Implements the core booking engine with:
1. Full atomicity — all items succeed or all fail (DB transaction)
2. Conflict detection using full service duration (not just start time)
3. Both caregiver AND patient overlap validation
4. Detailed error reporting — which slot failed and why

Design Decision: Pessimistic Locking via DB Transactions
-------------------------------------------------------
We use a database transaction (BEGIN...COMMIT/ROLLBACK) wrapping all
validation + insertion. For PostgreSQL, we would use SELECT ... FOR UPDATE
to acquire row-level locks on existing booking_items for the same caregiver/date.

For SQLite (dev mode), we rely on SQLite's serialized write behavior —
only one writer at a time — which provides equivalent atomicity guarantees.

Why NOT optimistic locking:
- Optimistic locking (version column + retry on conflict) introduces
  retry storms under concurrent load for the same caregiver.
- In healthcare, deterministic behavior > throughput.
- Pessimistic locking is simpler to reason about and test.

Overlap Formula (used everywhere):
    overlap = (new_start < existing_end) AND (existing_start < new_end)
    where end = start + duration_minutes
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service import Service
from app.models.caregiver import Caregiver
from app.models.patient import Patient
from app.models.caregiver_service import CaregiverService
from app.models.booking import Booking, BookingItem
from app.schemas.cart import (
    CheckoutRequest,
    CheckoutResponse,
    CheckoutItemResponse,
    CheckoutErrorResponse,
)


class ConflictError(Exception):
    """Raised when a booking conflict is detected during checkout."""

    def __init__(self, failed_items: list[dict], message: str = "Booking conflict"):
        self.failed_items = failed_items
        self.message = message
        super().__init__(message)


def _time_to_minutes(t: str) -> int:
    """Convert 'HH:MM' to minutes since midnight."""
    h, m = map(int, t.split(":"))
    return h * 60 + m


def _minutes_to_time(minutes: int) -> str:
    """Convert minutes since midnight to 'HH:MM'."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _has_overlap(start_a: int, dur_a: int, start_b: int, dur_b: int) -> bool:
    """
    Check if two time ranges overlap.

    [start_a, start_a + dur_a) vs [start_b, start_b + dur_b)

    Adjacent slots do NOT overlap:
    - 10:00-11:00 and 11:00-11:30 → False (correct: no overlap)
    """
    return start_a < (start_b + dur_b) and start_b < (start_a + dur_a)


async def perform_checkout(
    db: AsyncSession,
    request: CheckoutRequest,
) -> CheckoutResponse:
    """
    Execute an atomic checkout for a patient's cart.

    Steps:
    1. Validate patient exists
    2. Validate all services exist → fetch durations + prices
    3. Validate all caregivers exist and can perform their assigned services
    4. Intra-cart validation: detect overlaps within the cart itself
       - Patient self-overlap (same patient, same date, overlapping times)
       - Duplicate caregiver+time (same caregiver, same date, overlapping times)
    5. Database conflict detection: check against existing bookings
       - Caregiver conflicts (full duration overlap)
       - Patient conflicts (full duration overlap)
    6. If ANY conflict → raise ConflictError → transaction rolls back
    7. If all clear → create Booking + BookingItems → commit

    Raises:
        ConflictError: With detailed info about which item(s) caused conflicts.
        ValueError: For invalid input (missing service, caregiver, etc.)
    """
    failed_items: list[dict] = []

    patient_result = await db.execute(
        select(Patient).where(Patient.id == request.patient_id)
    )
    patient = patient_result.scalar_one_or_none()
    if patient is None:
        raise ValueError(f"Patient with id '{request.patient_id}' not found")

    service_ids = list(set(item.service_id for item in request.items))
    services_result = await db.execute(
        select(Service).where(Service.id.in_(service_ids))
    )
    services_map: dict[str, Service] = {
        s.id: s for s in services_result.scalars().all()
    }

    for i, item in enumerate(request.items):
        if item.service_id not in services_map:
            failed_items.append({
                "index": i,
                "reason": f"Service '{item.service_id}' not found",
                "slot_date": item.date,
                "start_time": item.start_time,
            })

    if failed_items:
        raise ConflictError(
            failed_items=failed_items,
            message="One or more services not found",
        )

    caregiver_ids = list(set(item.caregiver_id for item in request.items))
    caregivers_result = await db.execute(
        select(Caregiver).where(Caregiver.id.in_(caregiver_ids))
    )
    caregivers_map: dict[str, Caregiver] = {
        c.id: c for c in caregivers_result.scalars().all()
    }

    cg_services_result = await db.execute(
        select(CaregiverService).where(
            CaregiverService.caregiver_id.in_(caregiver_ids)
        )
    )
    cg_qualifications: set[tuple[str, str]] = {
        (cs.caregiver_id, cs.service_id) for cs in cg_services_result.scalars().all()
    }

    for i, item in enumerate(request.items):
        if item.caregiver_id not in caregivers_map:
            failed_items.append({
                "index": i,
                "reason": f"Caregiver '{item.caregiver_id}' not found",
                "slot_date": item.date,
                "start_time": item.start_time,
            })
        elif (item.caregiver_id, item.service_id) not in cg_qualifications:
            svc = services_map[item.service_id]
            cg = caregivers_map[item.caregiver_id]
            failed_items.append({
                "index": i,
                "reason": (
                    f"Caregiver '{cg.name}' is not qualified for "
                    f"service '{svc.name}'"
                ),
                "slot_date": item.date,
                "start_time": item.start_time,
            })

    if failed_items:
        raise ConflictError(
            failed_items=failed_items,
            message="Caregiver validation failed",
        )

    enriched_items = []
    for i, item in enumerate(request.items):
        svc = services_map[item.service_id]
        enriched_items.append({
            "index": i,
            "service_id": item.service_id,
            "caregiver_id": item.caregiver_id,
            "date": item.date,
            "start_minutes": _time_to_minutes(item.start_time),
            "duration": svc.duration_minutes,
            "start_time": item.start_time,
        })

    for i, a in enumerate(enriched_items):
        for j, b in enumerate(enriched_items):
            if j <= i:
                continue
            if a["caregiver_id"] == b["caregiver_id"] and a["date"] == b["date"]:
                if _has_overlap(
                    a["start_minutes"], a["duration"],
                    b["start_minutes"], b["duration"],
                ):
                    cg_name = caregivers_map[a["caregiver_id"]].name
                    failed_items.append({
                        "index": j,
                        "reason": (
                            f"Cart conflict: Caregiver '{cg_name}' is double-booked "
                            f"in your cart — item #{i+1} ({a['start_time']}) and "
                            f"item #{j+1} ({b['start_time']}) overlap on {a['date']}"
                        ),
                        "slot_date": b["date"],
                        "start_time": b["start_time"],
                    })

    for i, a in enumerate(enriched_items):
        for j, b in enumerate(enriched_items):
            if j <= i:
                continue
            if a["date"] == b["date"]:
                if _has_overlap(
                    a["start_minutes"], a["duration"],
                    b["start_minutes"], b["duration"],
                ):
                    already_flagged = any(
                        f["index"] == j and "Cart conflict" in f["reason"]
                        for f in failed_items
                    )
                    if not already_flagged:
                        svc_a = services_map[a["service_id"]].name
                        svc_b = services_map[b["service_id"]].name
                        failed_items.append({
                            "index": j,
                            "reason": (
                                f"Cart conflict: You have overlapping services — "
                                f"'{svc_a}' at {a['start_time']} and "
                                f"'{svc_b}' at {b['start_time']} on {a['date']}"
                            ),
                            "slot_date": b["date"],
                            "start_time": b["start_time"],
                        })

    if failed_items:
        raise ConflictError(
            failed_items=failed_items,
            message="Cart contains conflicting items",
        )

    dates = list(set(item.date for item in request.items))

    cg_bookings_query = (
        select(BookingItem)
        .join(Booking, BookingItem.booking_id == Booking.id)
        .where(
            BookingItem.caregiver_id.in_(caregiver_ids),
            BookingItem.slot_date.in_(dates),
            Booking.status == "confirmed",
        )
    )
    cg_bookings_result = await db.execute(cg_bookings_query)
    existing_cg_bookings = list(cg_bookings_result.scalars().all())

    patient_bookings_query = (
        select(BookingItem)
        .join(Booking, BookingItem.booking_id == Booking.id)
        .where(
            Booking.patient_id == request.patient_id,
            BookingItem.slot_date.in_(dates),
            Booking.status == "confirmed",
        )
    )
    patient_bookings_result = await db.execute(patient_bookings_query)
    existing_patient_bookings = list(patient_bookings_result.scalars().all())

    for ei in enriched_items:
        for eb in existing_cg_bookings:
            if (
                eb.caregiver_id == ei["caregiver_id"]
                and eb.slot_date == ei["date"]
            ):
                eb_start = _time_to_minutes(eb.start_time)
                if _has_overlap(
                    ei["start_minutes"], ei["duration"],
                    eb_start, eb.duration_minutes,
                ):
                    cg_name = caregivers_map[ei["caregiver_id"]].name
                    eb_end = _minutes_to_time(eb_start + eb.duration_minutes)
                    failed_items.append({
                        "index": ei["index"],
                        "reason": (
                            f"Caregiver '{cg_name}' is already booked from "
                            f"{eb.start_time} to {eb_end} on {ei['date']}"
                        ),
                        "slot_date": ei["date"],
                        "start_time": ei["start_time"],
                    })
                    break  # One conflict per item is enough

        for eb in existing_patient_bookings:
            if eb.slot_date == ei["date"]:
                eb_start = _time_to_minutes(eb.start_time)
                if _has_overlap(
                    ei["start_minutes"], ei["duration"],
                    eb_start, eb.duration_minutes,
                ):
                    eb_end = _minutes_to_time(eb_start + eb.duration_minutes)
                    failed_items.append({
                        "index": ei["index"],
                        "reason": (
                            f"You already have a booking from "
                            f"{eb.start_time} to {eb_end} on {ei['date']}"
                        ),
                        "slot_date": ei["date"],
                        "start_time": ei["start_time"],
                    })
                    break  # One conflict per item is enough

    if failed_items:
        raise ConflictError(
            failed_items=failed_items,
            message="Booking conflicts detected — entire checkout rolled back",
        )

    total_price = sum(
        float(services_map[item.service_id].price) for item in request.items
    )

    booking = Booking(
        patient_id=request.patient_id,
        total_price=total_price,
        status="confirmed",
    )
    db.add(booking)
    await db.flush()  # Generate booking.id

    response_items: list[CheckoutItemResponse] = []
    for item in request.items:
        svc = services_map[item.service_id]
        cg = caregivers_map[item.caregiver_id]

        bi = BookingItem(
            booking_id=booking.id,
            service_id=item.service_id,
            caregiver_id=item.caregiver_id,
            slot_date=item.date,
            start_time=item.start_time,
            duration_minutes=svc.duration_minutes,  # Snapshot
            price=float(svc.price),                 # Snapshot
        )
        db.add(bi)

        end_minutes = _time_to_minutes(item.start_time) + svc.duration_minutes
        response_items.append(
            CheckoutItemResponse(
                service_id=item.service_id,
                service_name=svc.name,
                caregiver_id=item.caregiver_id,
                caregiver_name=cg.name,
                date=item.date,
                start_time=item.start_time,
                end_time=_minutes_to_time(end_minutes),
                duration_minutes=svc.duration_minutes,
                price=float(svc.price),
            )
        )

    await db.commit()

    return CheckoutResponse(
        booking_id=booking.id,
        patient_id=request.patient_id,
        items=response_items,
        total_price=total_price,
        status="confirmed",
    )
