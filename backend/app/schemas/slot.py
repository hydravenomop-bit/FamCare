"""Slot availability schemas."""

from typing import List
from pydantic import BaseModel


class SlotAvailabilityRequest(BaseModel):
    """Query parameters for slot availability."""
    service_id: str
    date: str  # "YYYY-MM-DD"


class AvailableCaregiver(BaseModel):
    """A caregiver available for a specific slot."""
    id: str
    name: str


class SlotResponse(BaseModel):
    """A single available time slot with its available caregivers."""
    start_time: str       # "HH:MM"
    end_time: str         # "HH:MM"
    available_caregivers: List[AvailableCaregiver]


class SlotAvailabilityResponse(BaseModel):
    """Full availability response for a service on a date."""
    service_id: str
    service_name: str
    duration_minutes: int
    date: str
    slots: List[SlotResponse]
