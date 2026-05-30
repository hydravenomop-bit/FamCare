"""Service response schema."""

from typing import Optional
from pydantic import BaseModel


class ServiceResponse(BaseModel):
    """Response schema for a service."""
    id: str
    name: str
    duration_minutes: int
    price: float
    description: Optional[str] = None

    model_config = {"from_attributes": True}
