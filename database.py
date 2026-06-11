from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

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
# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./solarsats.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
