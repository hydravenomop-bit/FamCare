"""
Tests for conflict detection.

Verifies:
1. Caregiver conflicts use full duration (not just start time)
2. Patient self-overlap detection
3. Adjacent slots do NOT conflict
4. Intra-cart conflict detection
5. Error messages identify the specific conflicting slot
"""

import pytest
from httpx import AsyncClient

from tests.conftest import (
    PHYSIO_ID, WOUND_ID, IV_ID, CHECKUP_ID,
    ALICE_ID, BOB_ID, CAROL_ID, DAVID_ID, EVE_ID,
    JOHN_ID, JANE_ID, MIKE_ID,
)

CHECKOUT_URL = "/api/v1/cart/checkout"



@pytest.mark.asyncio
async def test_caregiver_exact_overlap(client: AsyncClient):
    """Two patients booking the same caregiver at the exact same time → conflict."""
    resp1 = await client.post(CHECKOUT_URL, json={
        "patient_id": JOHN_ID,
        "items": [{
            "service_id": PHYSIO_ID,
            "caregiver_id": ALICE_ID,
            "start_time": "10:00",
            "date": "2026-06-01",
        }],
    })
    assert resp1.status_code == 200

    resp2 = await client.post(CHECKOUT_URL, json={
        "patient_id": JANE_ID,
        "items": [{
            "service_id": PHYSIO_ID,
            "caregiver_id": ALICE_ID,
            "start_time": "10:00",
            "date": "2026-06-01",
        }],
    })
    assert resp2.status_code == 409
    assert "already booked" in resp2.json()["failed_items"][0]["reason"]


@pytest.mark.asyncio
async def test_caregiver_partial_overlap_duration_aware(client: AsyncClient):
    """
    60-min service at 10:00 blocks until 11:00.
    Booking at 10:30 should conflict (even though start times differ).

    This is THE critical test — ensures overlap check uses full duration.
    """
    resp1 = await client.post(CHECKOUT_URL, json={
        "patient_id": JOHN_ID,
        "items": [{
            "service_id": PHYSIO_ID,
            "caregiver_id": ALICE_ID,
            "start_time": "10:00",
            "date": "2026-06-01",
        }],
    })
    assert resp1.status_code == 200

    resp2 = await client.post(CHECKOUT_URL, json={
        "patient_id": JANE_ID,
        "items": [{
            "service_id": WOUND_ID,
            "caregiver_id": CAROL_ID,  # Carol does Wound Dressing
            "start_time": "10:30",
            "date": "2026-06-01",
        }],
    })
    assert resp2.status_code == 200

    resp3 = await client.post(CHECKOUT_URL, json={
        "patient_id": JANE_ID,
        "items": [{
            "service_id": PHYSIO_ID,
            "caregiver_id": ALICE_ID,
            "start_time": "10:30",
            "date": "2026-06-01",
        }],
    })
    assert resp3.status_code == 409


@pytest.mark.asyncio
async def test_caregiver_adjacent_slots_no_conflict(client: AsyncClient):
    """
    Adjacent slots should NOT conflict.
    Physiotherapy (60min) at 10:00 ends at 11:00.
    Wound Dressing (30min) at 11:00 should be allowed.
    """
    resp1 = await client.post(CHECKOUT_URL, json={
        "patient_id": JOHN_ID,
        "items": [{
            "service_id": PHYSIO_ID,
            "caregiver_id": ALICE_ID,
            "start_time": "10:00",
            "date": "2026-06-01",
        }],
    })
    assert resp1.status_code == 200

    resp2 = await client.post(CHECKOUT_URL, json={
        "patient_id": JANE_ID,
        "items": [{
            "service_id": CHECKUP_ID,
            "caregiver_id": ALICE_ID,
            "start_time": "11:00",
            "date": "2026-06-01",
        }],
    })
    assert resp2.status_code == 200  # 11:00 starts exactly when 10:00-11:00 ends


@pytest.mark.asyncio
async def test_caregiver_conflict_across_services(client: AsyncClient):
    """
    Caregiver conflict detection works across different services.
    Bob has IV Therapy (45min) at 14:00 → busy until 14:45.
    Bob can't do Wound Dressing at 14:30 even though it's a different service.
    """
    resp1 = await client.post(CHECKOUT_URL, json={
        "patient_id": JOHN_ID,
        "items": [{
            "service_id": IV_ID,
            "caregiver_id": BOB_ID,
            "start_time": "14:00",
            "date": "2026-06-01",
        }],
    })
    assert resp1.status_code == 200

    resp2 = await client.post(CHECKOUT_URL, json={
        "patient_id": JANE_ID,
        "items": [{
            "service_id": WOUND_ID,
            "caregiver_id": BOB_ID,
            "start_time": "14:30",
            "date": "2026-06-01",
        }],
    })
    assert resp2.status_code == 409



@pytest.mark.asyncio
async def test_patient_self_overlap_same_day(client: AsyncClient):
    """
    Patient cannot have two services overlapping on the same day.
    John has Physiotherapy (60min) at 10:00 → busy until 11:00.
    John can't have Wound Dressing at 10:30 even with a different caregiver.
    """
    resp1 = await client.post(CHECKOUT_URL, json={
        "patient_id": JOHN_ID,
        "items": [{
            "service_id": PHYSIO_ID,
            "caregiver_id": ALICE_ID,
            "start_time": "10:00",
            "date": "2026-06-01",
        }],
    })
    assert resp1.status_code == 200

    resp2 = await client.post(CHECKOUT_URL, json={
        "patient_id": JOHN_ID,
        "items": [{
            "service_id": WOUND_ID,
            "caregiver_id": CAROL_ID,
            "start_time": "10:30",
            "date": "2026-06-01",
        }],
    })
    assert resp2.status_code == 409
    assert "already have a booking" in resp2.json()["failed_items"][0]["reason"]


@pytest.mark.asyncio
async def test_patient_no_overlap_different_days(client: AsyncClient):
    """Patient CAN have services at the same time on DIFFERENT days."""
    response = await client.post(CHECKOUT_URL, json={
        "patient_id": JOHN_ID,
        "items": [
            {
                "service_id": PHYSIO_ID,
                "caregiver_id": ALICE_ID,
                "start_time": "10:00",
                "date": "2026-06-01",
            },
            {
                "service_id": PHYSIO_ID,
                "caregiver_id": ALICE_ID,
                "start_time": "10:00",
                "date": "2026-06-02",
            },
        ],
    })
    assert response.status_code == 200



@pytest.mark.asyncio
async def test_intracart_caregiver_overlap(client: AsyncClient):
    """
    Cart items that double-book the same caregiver should be rejected
    BEFORE hitting the database.
    """
    response = await client.post(CHECKOUT_URL, json={
        "patient_id": JOHN_ID,
        "items": [
            {
                "service_id": PHYSIO_ID,
                "caregiver_id": ALICE_ID,
                "start_time": "10:00",
                "date": "2026-06-01",
            },
            {
                "service_id": CHECKUP_ID,
                "caregiver_id": ALICE_ID,
                "start_time": "10:30",
                "date": "2026-06-01",
            },
        ],
    })
    assert response.status_code == 409
    assert "Cart conflict" in response.json()["failed_items"][0]["reason"]


@pytest.mark.asyncio
async def test_intracart_patient_overlap(client: AsyncClient):
    """
    Cart items that overlap for the same patient (different caregivers)
    should be rejected.
    """
    response = await client.post(CHECKOUT_URL, json={
        "patient_id": JOHN_ID,
        "items": [
            {
                "service_id": PHYSIO_ID,
                "caregiver_id": ALICE_ID,
                "start_time": "10:00",
                "date": "2026-06-01",
            },
            {
                "service_id": WOUND_ID,
                "caregiver_id": CAROL_ID,  # Different caregiver
                "start_time": "10:30",
                "date": "2026-06-01",
            },
        ],
    })
    assert response.status_code == 409



@pytest.mark.asyncio
async def test_error_identifies_conflicting_slot(client: AsyncClient):
    """Error response should identify which specific slot caused the conflict."""
    await client.post(CHECKOUT_URL, json={
        "patient_id": JOHN_ID,
        "items": [{
            "service_id": PHYSIO_ID,
            "caregiver_id": ALICE_ID,
            "start_time": "10:00",
            "date": "2026-06-01",
        }],
    })

    resp = await client.post(CHECKOUT_URL, json={
        "patient_id": JANE_ID,
        "items": [{
            "service_id": PHYSIO_ID,
            "caregiver_id": ALICE_ID,
            "start_time": "10:30",
            "date": "2026-06-01",
        }],
    })
    assert resp.status_code == 409
    failed = resp.json()["failed_items"][0]
    assert failed["slot_date"] == "2026-06-01"
    assert failed["start_time"] == "10:30"
    assert "Alice" in failed["reason"]
    assert "10:00" in failed["reason"]  # Should mention the conflicting booking
    assert "11:00" in failed["reason"]  # Should mention end time
