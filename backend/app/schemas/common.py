"""Common schemas — shared error structures."""

from typing import Optional, List
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Detail about a specific error within a checkout."""
    item_index: int
    service_name: Optional[str] = None
    slot_date: str
    start_time: str
    reason: str


class ErrorResponse(BaseModel):
    """Generic error response."""
    error: str
    message: str
    details: Optional[List[ErrorDetail]] = None
