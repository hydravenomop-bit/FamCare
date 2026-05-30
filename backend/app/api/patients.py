"""
Patients API — list patients (simplified, no authentication).

GET /patients → all patients
"""

from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models.patient import Patient


class PatientResponse(BaseModel):
    id: str
    name: str
    phone: Optional[str] = None

    model_config = {"from_attributes": True}


router = APIRouter()


@router.get("", response_model=list[PatientResponse])
async def list_patients(db: AsyncSession = Depends(get_db)):
    """
    List all patients.

    In a production system, this would be behind authentication.
    For this assignment, patients are pre-seeded and selected by the user.
    """
    result = await db.execute(select(Patient).order_by(Patient.name))
    patients = result.scalars().all()
    return [PatientResponse.model_validate(p) for p in patients]
