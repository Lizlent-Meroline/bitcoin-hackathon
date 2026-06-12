"""Database models for persisted meter payments and producers."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    producer_id: Mapped[str] = mapped_column(String, nullable=False)
    consumer_id: Mapped[str] = mapped_column(String, nullable=False)
    kwh: Mapped[float] = mapped_column(Float, nullable=False)
    sats_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    invoice: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )


class Producer(Base):
    __tablename__ = "producers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    lightning_address: Mapped[str] = mapped_column(String, nullable=False)
    total_earned: Mapped[int] = mapped_column(Integer, default=0)
