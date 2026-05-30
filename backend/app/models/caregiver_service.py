"""
CaregiverService — M2M association table.

Maps which caregivers are qualified to perform which services.
A caregiver can perform multiple services; a service can be performed by multiple caregivers.
"""

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CaregiverService(Base):
    __tablename__ = "caregiver_services"

    caregiver_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("caregivers.id", ondelete="CASCADE"),
        primary_key=True,
    )
    service_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("services.id", ondelete="CASCADE"),
        primary_key=True,
    )

    caregiver = relationship("Caregiver", back_populates="service_links")
    service = relationship("Service", back_populates="caregiver_links")

    def __repr__(self) -> str:
        return f"<CaregiverService caregiver={self.caregiver_id} service={self.service_id}>"
