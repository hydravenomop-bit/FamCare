"""
Caregiver model — represents a healthcare professional who provides services.

Caregivers are linked to services they can perform via the CaregiverService M2M table.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Caregiver(Base):
    __tablename__ = "caregivers"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    service_links = relationship("CaregiverService", back_populates="caregiver")
    booking_items = relationship("BookingItem", back_populates="caregiver")

    def __repr__(self) -> str:
        return f"<Caregiver {self.name}>"
