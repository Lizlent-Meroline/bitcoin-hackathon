from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    producer_id = Column(String, nullable=False)
    consumer_id = Column(String, nullable=False)
    kwh = Column(Float, nullable=False)
    sats_amount = Column(Integer, nullable=False)
    invoice = Column(String, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

class Producer(Base):
    __tablename__ = "producers"
    
    id = Column(String, primary_key=True)
    lightning_address = Column(String, nullable=False)
    total_earned = Column(Integer, default=0)
    # created_at removed for simplicity
