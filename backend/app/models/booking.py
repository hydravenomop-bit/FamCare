"""
Booking and BookingItem models — represent a completed checkout transaction.

A Booking is a single atomic checkout for one patient.
BookingItems are the individual service slots within that booking.

Key design:
- duration_minutes and price are SNAPSHOTS — captured at booking time
  so changes to the service definition don't retroactively affect bookings.
- start_time is stored as a string "HH:MM" for SQLite compatibility.
  In PostgreSQL, this would be a TIME column.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    Numeric,
    DateTime,
    Date,
    ForeignKey,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Booking(Base):
    """
    A single checkout transaction.
    Contains 1..N BookingItems — all succeed or all fail (atomic).
    """

    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id"), nullable=False
    )
    total_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="confirmed"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    patient = relationship("Patient", back_populates="bookings")
    items = relationship(
        "BookingItem", back_populates="booking", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('confirmed', 'cancelled')", name="ck_booking_status"
        ),
        Index("idx_bookings_patient", "patient_id"),
    )

    def __repr__(self) -> str:
        return f"<Booking {self.id[:8]} patient={self.patient_id[:8]} ${self.total_price}>"


class BookingItem(Base):
    """
    A single slot within a booking.

    Stores snapshots of duration and price from the service definition
    at the time of booking — so future service changes don't affect
    existing bookings.
    """

    __tablename__ = "booking_items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    booking_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False
    )
    service_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("services.id"), nullable=False
    )
    caregiver_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("caregivers.id"), nullable=False
    )
    slot_date: Mapped[str] = mapped_column(
        String(10), nullable=False  # "YYYY-MM-DD" — SQLite-friendly
    )
    start_time: Mapped[str] = mapped_column(
        String(5), nullable=False  # "HH:MM" — SQLite-friendly
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    booking = relationship("Booking", back_populates="items")
    service = relationship("Service", back_populates="booking_items")
    caregiver = relationship("Caregiver", back_populates="booking_items")

    __table_args__ = (
        Index("idx_bi_caregiver_date", "caregiver_id", "slot_date"),
        Index("idx_bi_booking_date", "booking_id", "slot_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<BookingItem {self.slot_date} {self.start_time} "
            f"duration={self.duration_minutes}min>"
        )
