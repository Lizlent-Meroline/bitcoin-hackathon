from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import Payment, Producer
from config import config
from meter import process_meter_reading

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

class ProducerRegisterRequest(BaseModel):
    producer_id: str
    lightning_address: str

@router.post("/meter/reading")
async def handle_meter_reading(
    reading: MeterReadingRequest,
    db: Session = Depends(get_db)
):
    """Handle incoming meter readings from smart meters"""
    
    # Process the meter reading with HMAC verification
    success, payment, message = await process_meter_reading(
        meter_id=reading.meter_id,
        kwh_delta=reading.kwh_delta,
        timestamp=reading.timestamp,
        signature=reading.signature,
        db=db
    )
    
    if not success:
        raise HTTPException(status_code=401, detail=message)
    
    # TODO: Create Lightning invoice via teammate's lightning.py
    # invoice = await create_invoice(payment.sats_amount)
    
    return {
        "message": message,
        "payment_id": payment.id,
        "sats": payment.sats_amount,
        "status": payment.status
    }

@router.get("/producer/{producer_id}/stats")
async def get_producer_stats(producer_id: str, db: Session = Depends(get_db)):
    """Get total earnings for a producer"""
    
    total_sats = db.query(func.sum(Payment.sats_amount)).filter(
        Payment.producer_id == producer_id,
        Payment.status == "paid"
    ).scalar() or 0
    
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
async def register_producer(
    producer_id: str, 
    lightning_address: str, 
    db: Session = Depends(get_db)
):
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
