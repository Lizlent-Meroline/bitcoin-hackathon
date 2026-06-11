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
    
    return {
        "message": f"✅ Meter reading received: {reading.kwh_delta} kWh = {sats_amount} sats",
        "payment_id": payment.id,
        "sats": sats_amount,
        "status": "pending"
    }

@router.get("/producer/{producer_id}/stats")
async def get_producer_stats(producer_id: str, db: Session = Depends(get_db)):
    """Get total earnings for a producer"""
    
    total_sats = db.query(Payment).filter(
        Payment.producer_id == producer_id,
        Payment.status == "paid"
    ).with_entities(func.sum(Payment.sats_amount)).scalar() or 0
    
    return {
        "producer_id": producer_id,
        "total_sats": total_sats,
        "total_kwh": total_sats / config.SATOSHIS_PER_KWH,
        "status": "active"
    }

@router.get("/producer/{producer_id}/history")
async def get_payment_history(producer_id: str, db: Session = Depends(get_db)):
    """Get payment history for a producer"""
    
    payments = db.query(Payment).filter(
        Payment.producer_id == producer_id
    ).order_by(Payment.created_at.desc()).limit(50).all()
    
    return {
        "producer_id": producer_id,
        "total_count": len(payments),
        "payments": [
            {
                "id": p.id,
                "kwh": p.kwh,
                "sats": p.sats_amount,
                "status": p.status,
                "created_at": p.created_at.isoformat()
            }
            for p in payments
        ]
    }

@router.post("/producer/register")
async def register_producer(producer_id: str, lightning_address: str, db: Session = Depends(get_db)):
    """Register a new producer"""
    
    producer = Producer(
        id=producer_id,
        lightning_address=lightning_address
    )
    
    db.merge(producer)
    db.commit()
    
    return {
        "message": "Producer registered successfully",
        "producer_id": producer_id,
        "lightning_address": lightning_address
    }

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "solarsats-backend"}

# Add import for meter functions
from meter import process_meter_reading

