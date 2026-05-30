"""
Service model — represents a bookable healthcare service.

Each service has a fixed duration (in 15-min increments) and a price per session.
Duration is NEVER hardcoded — always read from this table.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Numeric, Text, DateTime, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Service(Base):
    __tablename__ = "services"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    caregiver_links = relationship("CaregiverService", back_populates="service")
    booking_items = relationship("BookingItem", back_populates="service")

    __table_args__ = (
        CheckConstraint("duration_minutes > 0", name="ck_duration_positive"),
        CheckConstraint("duration_minutes % 15 = 0", name="ck_duration_15min_aligned"),
        CheckConstraint("price > 0", name="ck_price_positive"),
    )

    def __repr__(self) -> str:
        return f"<Service {self.name} ({self.duration_minutes}min, ${self.price})>"
