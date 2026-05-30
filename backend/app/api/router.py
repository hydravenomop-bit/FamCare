"""
Main API router — aggregates all sub-routers.
"""

from fastapi import APIRouter

from app.api.services import router as services_router
from app.api.caregivers import router as caregivers_router
from app.api.slots import router as slots_router
from app.api.cart import router as cart_router
from app.api.patients import router as patients_router

router = APIRouter()

router.include_router(services_router, prefix="/services", tags=["Services"])
router.include_router(caregivers_router, prefix="/caregivers", tags=["Caregivers"])
router.include_router(patients_router, prefix="/patients", tags=["Patients"])
router.include_router(slots_router, prefix="/slots", tags=["Slots"])
router.include_router(cart_router, prefix="/cart", tags=["Cart"])
