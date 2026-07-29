"""Verify an uploaded invoice image against the database.

Two clear stages, matching the project's "read, then decide with rules" design:
1. OCR (Tesseract) READS the text off the image.
2. Plain Python VERIFIES the extracted order number + total against the real
   order in the database. The "genuine vs fake" decision is deterministic, so
   an edited/forged invoice won't match our records and won't verify.

Works fully offline and free -- a good fit because our invoices are clean,
digitally-rendered images that OCR reads accurately.
"""

import io
import os
import re

import pytesseract
from loguru import logger
from PIL import Image

from app.database import SessionLocal
from app.models import Order

# Point pytesseract at the Tesseract binary (winget / UB-Mannheim default
# install location) in case it isn't on PATH for this process.
for _path in (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
):
    if os.path.exists(_path):
        pytesseract.pytesseract.tesseract_cmd = _path
        break

TOTAL_TOLERANCE = 0.5
_AMOUNT = re.compile(r"([\d,]+\.\d{2})")


def _extract_with_ocr(image_bytes: bytes) -> dict:
    """OCR the image and pull out invoice fields."""
    image = Image.open(io.BytesIO(image_bytes))
    text = pytesseract.image_to_string(image)
    lowered = text.lower()

    # It's (probably) one of our invoices if it carries the tell-tale words.
    is_invoice = ("shopsphere" in lowered or "invoice" in lowered) and (
        "order" in lowered or "total" in lowered
    )

    order_match = re.search(r"order\s*#?\s*(\d+)", lowered)
    order_id = int(order_match.group(1)) if order_match else None

    # Grand total = the amount on the last line mentioning "total"; fall back
    # to the largest money amount on the page.
    total = None
    for line in text.splitlines():
        if "total" in line.lower():
            amount = _AMOUNT.search(line)
            if amount:
                total = float(amount.group(1).replace(",", ""))
    if total is None:
        amounts = [float(a.replace(",", "")) for a in _AMOUNT.findall(text)]
        total = max(amounts) if amounts else None

    return {"is_invoice": is_invoice, "order_id": order_id, "total": total}


def verify_invoice(image_bytes: bytes, mime_type: str = "image/png") -> dict:
    """Return a verification result: status is one of
    'verified' | 'not_verified' | 'not_recognized' | 'error'."""
    try:
        extracted = _extract_with_ocr(image_bytes)
    except Exception as e:
        logger.error(f"OCR invoice read failed: {e}")
        return {"status": "error", "message": "I couldn't read that image. Please try again."}

    if not extracted["is_invoice"] or extracted["order_id"] is None:
        return {
            "status": "not_recognized",
            "message": "That doesn't look like a ShopSphere invoice. Please upload a valid invoice image.",
        }

    order_id = extracted["order_id"]
    total = extracted["total"]

    db = SessionLocal()
    try:
        order = db.get(Order, order_id)
        if order is None:
            return {
                "status": "not_verified",
                "message": "We couldn't find this invoice in our records, so it can't be verified.",
            }
        # Fake/edited check: the invoice total must match the recorded total.
        if total is None or abs(total - order.total_amount) > TOTAL_TOLERANCE:
            return {
                "status": "not_verified",
                "message": "The details on this invoice don't match our records, so it can't be verified.",
            }

        # Genuine -- return the trustworthy details straight from the database.
        return {
            "status": "verified",
            "message": "Invoice verified — this is a genuine ShopSphere order.",
            "order": {
                "order_id": order.id,
                "date": order.order_date.strftime("%Y-%m-%d"),
                "customer": order.customer.name,
                "items": [f"{it.quantity} x {it.product.name}" for it in order.items],
                "total": round(order.total_amount, 2),
                "order_status": order.status,
            },
        }
    finally:
        db.close()
