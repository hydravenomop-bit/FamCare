"""
Cart API — atomic checkout endpoint.

POST /cart/checkout

Accepts a cart of items and either books ALL of them or NONE.
Returns detailed error information when conflicts are detected.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.cart import CheckoutRequest, CheckoutResponse, CheckoutErrorResponse
from app.services.checkout import perform_checkout, ConflictError

router = APIRouter()


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    responses={
        409: {
            "model": CheckoutErrorResponse,
            "description": "Booking conflict — entire checkout rolled back",
        },
    },
)
async def checkout(
    request: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Atomic checkout — books all items in the cart or none.

    **Atomicity guarantee**: If ANY item fails validation (caregiver conflict,
    patient conflict, invalid data), the ENTIRE checkout is rolled back.
    No partial bookings. Ever.

    **Conflict detection**: Uses full service duration for overlap checks.
    A 60-min service at 10:00 blocks the caregiver until 11:00.

    **Error response (409)**: Returns exactly which item(s) caused the
    conflict and why, so the patient can fix their cart and retry.
    """
    try:
        result = await perform_checkout(db, request)
        return result
    except ConflictError as e:
        return JSONResponse(
            status_code=409,
            content=CheckoutErrorResponse(
                error="conflict",
                message=e.message,
                failed_items=e.failed_items,
            ).model_dump(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
