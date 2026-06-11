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
    
