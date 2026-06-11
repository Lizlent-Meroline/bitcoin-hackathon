from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime

from database import get_db, Payment, Producer
from config import config

router = APIRouter()

# Pydantic models for request/response
class MeterReadingRequest(BaseModel):
    meter_id: str
    kwh_delta: float
    timestamp: int
    signature: str

class PaymentResponse(BaseModel):
    payment_id: int
    invoice: str
    sats: int
    status: str

@router.post("/meter/reading")
async def handle_meter_reading(
    reading: MeterReadingRequest,
    db: Session = Depends(get_db)
):
    """Handle incoming meter readings from smart meters"""
    
    # Calculate sats (50 sats per kWh)
    sats_amount = int(reading.kwh_delta * config.SATOSHIS_PER_KWH)
    
    # TODO: Verify HMAC signature (waiting for teammate's utils.py)
    # For now, assume valid
    
    # Create payment record
    payment = Payment(
        producer_id=reading.meter_id,
        consumer_id="consumer-001",
        kwh=reading.kwh_delta,
        sats_amount=sats_amount,
        invoice="pending",
        status="pending"
    )
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    # TODO: Create Lightning invoice via teammate's lightning.py
    # invoice = await create_invoice(sats_amount)
    
