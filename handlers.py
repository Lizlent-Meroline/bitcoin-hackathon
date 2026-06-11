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

