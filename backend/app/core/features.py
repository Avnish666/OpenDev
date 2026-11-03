from fastapi import HTTPException
from app.core.config import settings


def require_receipts():
    if not settings.RECEIPT_PROCESSING_ENABLED:
        raise HTTPException(503,'Receipt uploads and processing are currently unavailable')


def require_checkout():
    if not settings.CHECKOUT_ENABLED:
        raise HTTPException(503,'Payment checkout is currently unavailable')
