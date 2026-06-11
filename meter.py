import hmac
import hashlib
from datetime import datetime
from typing import Optional, Tuple

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session

from config import config
from database import get_db
from models import Payment


def verify_hmac_signature(meter_id: str, kwh_delta: float, timestamp: int, signature: str) -> bool:
    """
    Verify HMAC signature from smart meter
    Prevents fake meter readings from stealing sats
    """
    # Create message string
    message = f"{meter_id}:{kwh_delta}:{timestamp}"
    
    # Generate expected signature using secret key
    expected = hmac.new(
        config.SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures (constant time comparison)
    return hmac.compare_digest(expected, signature)


async def process_meter_reading(
    meter_id: str,
    kwh_delta: float,
    timestamp: int,
    signature: str,
    db: Session
) -> Tuple[bool, Optional[Payment], str]:
    """
    Process a meter reading:
    1. Verify signature
    2. Calculate sats
    3. Create payment record
    4. Return result
    """
    # Step 1: Verify HMAC signature
    if not verify_hmac_signature(meter_id, kwh_delta, timestamp, signature):
        return False, None, "Invalid HMAC signature - possible tampering detected"
    
    # Step 2: Check if reading is positive (can't have negative energy)
    if kwh_delta <= 0:
        return False, None, "Invalid kWh delta - must be positive"
    
    # Step 3: Calculate sats (50 sats per kWh)
    sats_amount = int(kwh_delta * config.SATOSHIS_PER_KWH)
    
    # Step 4: Create payment record
    payment = Payment(
        producer_id=meter_id,
        consumer_id="consumer-001",  # Will come from request
        kwh=kwh_delta,
        sats_amount=sats_amount,
        invoice="pending",
        status="pending"
    )
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    return True, payment, f"Valid reading: {kwh_delta} kWh = {sats_amount} sats"


def generate_hmac_signature(meter_id: str, kwh_delta: float, timestamp: int) -> str:
    """
    Generate HMAC signature for a meter reading
    Used by smart meters to sign their readings
    This is a helper for testing - meters will implement this
    """
    message = f"{meter_id}:{kwh_delta}:{timestamp}"
    
    signature = hmac.new(
        config.SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return signature

