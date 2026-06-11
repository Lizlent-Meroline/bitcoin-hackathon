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

