"""Cart and checkout schemas."""

from typing import List, Dict, Any
from pydantic import BaseModel, field_validator
import re


class CartItemRequest(BaseModel):
    """A single item in the checkout cart."""
    service_id: str
    caregiver_id: str
    start_time: str   # "HH:MM" — must be 15-min aligned
    date: str          # "YYYY-MM-DD"

    @field_validator("start_time")
    @classmethod
    def validate_start_time(cls, v: str) -> str:
        if not re.match(r"^\d{2}:\d{2}$", v):
            raise ValueError("start_time must be in HH:MM format")
        hours, minutes = map(int, v.split(":"))
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError("Invalid time")
        if minutes % 15 != 0:
            raise ValueError("start_time must be 15-minute aligned (00, 15, 30, 45)")
        return v

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("date must be in YYYY-MM-DD format")
        return v


class CheckoutRequest(BaseModel):
    """Full checkout request — one patient, multiple items."""
    patient_id: str
    items: List[CartItemRequest]

    @field_validator("items")
    @classmethod
    def validate_items_not_empty(cls, v: list) -> list:
        if len(v) == 0:
            raise ValueError("Cart must contain at least one item")
        return v


class CheckoutItemResponse(BaseModel):
    """A single confirmed booking item in the response."""
    service_id: str
    service_name: str
    caregiver_id: str
    caregiver_name: str
    date: str
    start_time: str
    end_time: str
    duration_minutes: int
    price: float


class CheckoutResponse(BaseModel):
    """Successful checkout response."""
    booking_id: str
    patient_id: str
    items: List[CheckoutItemResponse]
    total_price: float
    status: str = "confirmed"


class CheckoutErrorResponse(BaseModel):
    """Failed checkout response — details which slot caused the failure."""
    error: str = "conflict"
    message: str
    failed_items: List[Dict[str, Any]]  # [{index, reason, slot_date, start_time}]
