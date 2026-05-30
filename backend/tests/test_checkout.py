"""
Tests for atomic checkout behavior.

Verifies:
1. Happy path — multi-item checkout succeeds
2. Full rollback — no partial bookings ever
3. Booking data integrity — snapshots, totals, status
4. Invalid input handling
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
async def test_checkout_happy_path_single_item(client: AsyncClient):
    """Single item checkout should succeed and return booking details."""
    response = await client.post(CHECKOUT_URL, json={
        "patient_id": JOHN_ID,
        "items": [
            {
                "service_id": PHYSIO_ID,
                "caregiver_id": ALICE_ID,
                "start_time": "10:00",
                "date": "2026-06-01",
            }
        ],
    })

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"
    assert data["patient_id"] == JOHN_ID
    assert len(data["items"]) == 1
    assert data["items"][0]["service_name"] == "Physiotherapy"
    assert data["items"][0]["caregiver_name"] == "Alice Sharma"
    assert data["items"][0]["start_time"] == "10:00"
    assert data["items"][0]["end_time"] == "11:00"  # 60 min duration
    assert data["items"][0]["duration_minutes"] == 60
    assert data["total_price"] == 1500.00


@pytest.mark.asyncio
async def test_checkout_happy_path_multi_item(client: AsyncClient):
    """
    Multi-item checkout (the example from the assignment):
    - Physiotherapy 60min Mon 10:00
    - Wound Dressing 30min Mon 15:00
    - Physiotherapy 60min Wed 10:00
    """
    response = await client.post(CHECKOUT_URL, json={
        "patient_id": JOHN_ID,
        "items": [
            {
                "service_id": PHYSIO_ID,
                "caregiver_id": ALICE_ID,
                "start_time": "10:00",
                "date": "2026-06-01",  # Monday
            },
            {
                "service_id": WOUND_ID,
                "caregiver_id": BOB_ID,
                "start_time": "15:00",
                "date": "2026-06-01",  # Monday
            },
            {
                "service_id": PHYSIO_ID,
                "caregiver_id": ALICE_ID,
                "start_time": "10:00",
                "date": "2026-06-03",  # Wednesday
            },
        ],
    })

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"
    assert len(data["items"]) == 3
    assert data["total_price"] == 3500.00


@pytest.mark.asyncio
async def test_checkout_full_rollback_on_conflict(client: AsyncClient):
    """
    If ANY item fails, ENTIRE checkout rolls back.

    1. John books Alice for Physiotherapy Mon 10:00 (succeeds)
    2. Jane tries to book: Alice Mon 10:30 (conflict) + Bob Mon 15:00 (would succeed)
    3. Result: 409, BOTH items rolled back, Bob 15:00 is NOT booked
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
        "items": [
            {
                "service_id": WOUND_ID,
                "caregiver_id": BOB_ID,
                "start_time": "15:00",
                "date": "2026-06-01",
            },
            {
                "service_id": PHYSIO_ID,
                "caregiver_id": ALICE_ID,
                "start_time": "10:30",
                "date": "2026-06-01",
            },
        ],
    })
    assert resp2.status_code == 409
    data = resp2.json()
    assert data["error"] == "conflict"
    assert len(data["failed_items"]) > 0

    resp3 = await client.post(CHECKOUT_URL, json={
        "patient_id": JANE_ID,
        "items": [{
            "service_id": WOUND_ID,
            "caregiver_id": BOB_ID,
            "start_time": "15:00",
            "date": "2026-06-01",
        }],
    })
    assert resp3.status_code == 200  # Proves rollback worked


@pytest.mark.asyncio
async def test_checkout_snapshots_duration_and_price(client: AsyncClient):
    """Booking items should snapshot duration and price from the service."""
    response = await client.post(CHECKOUT_URL, json={
        "patient_id": JOHN_ID,
        "items": [{
            "service_id": IV_ID,
            "caregiver_id": BOB_ID,
            "start_time": "14:00",
            "date": "2026-06-01",
        }],
    })

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["duration_minutes"] == 45  # IV Therapy duration
    assert item["price"] == 2000.00        # IV Therapy price
    assert item["end_time"] == "14:45"     # 14:00 + 45min


@pytest.mark.asyncio
async def test_checkout_empty_cart_rejected(client: AsyncClient):
    """Empty cart should be rejected with 422."""
    response = await client.post(CHECKOUT_URL, json={
        "patient_id": JOHN_ID,
        "items": [],
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_checkout_invalid_patient(client: AsyncClient):
    """Non-existent patient should return 400."""
    response = await client.post(CHECKOUT_URL, json={
        "patient_id": "nonexistent-patient-id",
        "items": [{
            "service_id": PHYSIO_ID,
            "caregiver_id": ALICE_ID,
            "start_time": "10:00",
            "date": "2026-06-01",
        }],
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_checkout_invalid_service(client: AsyncClient):
    """Non-existent service should return 409 with details."""
    response = await client.post(CHECKOUT_URL, json={
        "patient_id": JOHN_ID,
        "items": [{
            "service_id": "nonexistent-service-id",
            "caregiver_id": ALICE_ID,
            "start_time": "10:00",
            "date": "2026-06-01",
        }],
    })
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_checkout_unqualified_caregiver(client: AsyncClient):
    """Caregiver not qualified for the service should be rejected."""
    response = await client.post(CHECKOUT_URL, json={
        "patient_id": JOHN_ID,
        "items": [{
            "service_id": IV_ID,
            "caregiver_id": ALICE_ID,
            "start_time": "10:00",
            "date": "2026-06-01",
        }],
    })
    assert response.status_code == 409
    assert "not qualified" in response.json()["failed_items"][0]["reason"]


@pytest.mark.asyncio
async def test_checkout_misaligned_time_rejected(client: AsyncClient):
    """Non-15-min-aligned start time should be rejected with 422."""
    response = await client.post(CHECKOUT_URL, json={
        "patient_id": JOHN_ID,
        "items": [{
            "service_id": PHYSIO_ID,
            "caregiver_id": ALICE_ID,
            "start_time": "10:07",
            "date": "2026-06-01",
        }],
    })
    assert response.status_code == 422
