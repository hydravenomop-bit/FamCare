"""
Tests for slot availability.

Verifies:
1. Available slots are 15-min aligned
2. Duration-aware slot generation (60min service doesn't show 19:30)
3. Slots disappear after booking
4. Different caregivers have independent availability
5. Service not found returns 404
"""

import pytest
from httpx import AsyncClient

from tests.conftest import (
    PHYSIO_ID, WOUND_ID, IV_ID, CHECKUP_ID,
    ALICE_ID, BOB_ID, CAROL_ID,
    JOHN_ID, JANE_ID,
)

SLOTS_URL = "/api/v1/slots/available"
CHECKOUT_URL = "/api/v1/cart/checkout"


@pytest.mark.asyncio
async def test_slots_returns_available_times(client: AsyncClient):
    """Should return available slots for a service on a date."""
    resp = await client.get(SLOTS_URL, params={
        "service_id": PHYSIO_ID,
        "date": "2026-06-01",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["service_id"] == PHYSIO_ID
    assert data["service_name"] == "Physiotherapy"
    assert data["duration_minutes"] == 60
    assert data["date"] == "2026-06-01"
    assert len(data["slots"]) > 0

    for slot in data["slots"]:
        minutes = int(slot["start_time"].split(":")[1])
        assert minutes % 15 == 0, f"Slot {slot['start_time']} not 15-min aligned"


@pytest.mark.asyncio
async def test_slots_duration_aware_no_overflow(client: AsyncClient):
    """
    60-min service should not show slots where the service would end
    after business hours (20:00).

    Last valid slot for 60min: 19:00 (ends at 20:00).
    19:15 should NOT appear.
    """
    resp = await client.get(SLOTS_URL, params={
        "service_id": PHYSIO_ID,  # 60 min
        "date": "2026-06-01",
    })
    data = resp.json()
    start_times = [s["start_time"] for s in data["slots"]]

    assert "19:00" in start_times, "19:00 should be available (ends at 20:00)"
    assert "19:15" not in start_times, "19:15 would end at 20:15 — past business hours"
    assert "19:30" not in start_times
    assert "19:45" not in start_times


@pytest.mark.asyncio
async def test_slots_30min_service_more_options(client: AsyncClient):
    """30-min service should have more available slots than 60-min service."""
    resp_60 = await client.get(SLOTS_URL, params={
        "service_id": PHYSIO_ID,  # 60 min
        "date": "2026-06-01",
    })
    resp_30 = await client.get(SLOTS_URL, params={
        "service_id": WOUND_ID,  # 30 min
        "date": "2026-06-01",
    })
    slots_60 = resp_60.json()["slots"]
    slots_30 = resp_30.json()["slots"]

    assert len(slots_30) > len(slots_60), (
        "30-min service should have more available start times than 60-min service"
    )


@pytest.mark.asyncio
async def test_slots_disappear_after_booking(client: AsyncClient):
    """After booking a caregiver at a time, that slot should no longer show them."""
    resp1 = await client.get(SLOTS_URL, params={
        "service_id": PHYSIO_ID,
        "date": "2026-06-01",
    })
    initial_slots = resp1.json()["slots"]

    slot_10 = next(s for s in initial_slots if s["start_time"] == "10:00")
    alice_initially_available = any(
        c["name"] == "Alice Sharma" for c in slot_10["available_caregivers"]
    )
    assert alice_initially_available, "Alice should be available at 10:00 initially"

    await client.post(CHECKOUT_URL, json={
        "patient_id": JOHN_ID,
        "items": [{
            "service_id": PHYSIO_ID,
            "caregiver_id": ALICE_ID,
            "start_time": "10:00",
            "date": "2026-06-01",
        }],
    })

    resp2 = await client.get(SLOTS_URL, params={
        "service_id": PHYSIO_ID,
        "date": "2026-06-01",
    })
    updated_slots = resp2.json()["slots"]

    slot_10_updated = next(
        (s for s in updated_slots if s["start_time"] == "10:00"), None
    )
    if slot_10_updated:
        alice_still_available = any(
            c["name"] == "Alice Sharma" for c in slot_10_updated["available_caregivers"]
        )
        assert not alice_still_available, "Alice should NOT be available at 10:00 after booking"

    for blocked_time in ["10:15", "10:30", "10:45"]:
        blocked_slot = next(
            (s for s in updated_slots if s["start_time"] == blocked_time), None
        )
        if blocked_slot:
            alice_in_blocked = any(
                c["name"] == "Alice Sharma"
                for c in blocked_slot["available_caregivers"]
            )
            assert not alice_in_blocked, (
                f"Alice should NOT be available at {blocked_time} "
                f"(within 60min booking starting at 10:00)"
            )


@pytest.mark.asyncio
async def test_slots_other_caregivers_still_available(client: AsyncClient):
    """Booking one caregiver should not affect other caregivers' availability."""
    await client.post(CHECKOUT_URL, json={
        "patient_id": JOHN_ID,
        "items": [{
            "service_id": PHYSIO_ID,
            "caregiver_id": ALICE_ID,
            "start_time": "10:00",
            "date": "2026-06-01",
        }],
    })

    resp = await client.get(SLOTS_URL, params={
        "service_id": PHYSIO_ID,
        "date": "2026-06-01",
    })
    slot_10 = next(
        s for s in resp.json()["slots"] if s["start_time"] == "10:00"
    )
    caregiver_names = [c["name"] for c in slot_10["available_caregivers"]]
    assert "Alice Sharma" not in caregiver_names
    assert "Carol Mehta" in caregiver_names
    assert "Eve Singh" in caregiver_names


@pytest.mark.asyncio
async def test_slots_service_not_found(client: AsyncClient):
    """Non-existent service should return 404."""
    resp = await client.get(SLOTS_URL, params={
        "service_id": "nonexistent-id",
        "date": "2026-06-01",
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_slots_shows_caregivers(client: AsyncClient):
    """Each slot should list the caregivers available for it."""
    resp = await client.get(SLOTS_URL, params={
        "service_id": PHYSIO_ID,
        "date": "2026-06-01",
    })
    data = resp.json()
    first_slot = data["slots"][0]

    assert len(first_slot["available_caregivers"]) > 0
    for cg in first_slot["available_caregivers"]:
        assert "id" in cg
        assert "name" in cg
