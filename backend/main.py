"""SolarSats FastAPI backend.

Run from the repository root:
    python -m uvicorn backend.main:app --reload

Or from inside the backend directory:
    python -m uvicorn main:app --reload
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import os
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING
from enum import Enum
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

try:
    from .lightning import LightningError, lightning
    from .socket_manager import manager
except ImportError:
    from lightning import LightningError, lightning
    from socket_manager import manager


SATS_PER_KWH = Decimal("50")
METER_HMAC_SECRET = os.getenv("METER_HMAC_SECRET")

app = FastAPI(
    title="SolarSats API",
    description="Instant peer-to-peer solar settlement over Lightning HODL invoices.",
    version="0.1.0",
)


class TradeStatus(str, Enum):
    OPEN = "OPEN"
    FUNDED = "FUNDED"
    SETTLED = "SETTLED"
    CANCELED = "CANCELED"


class CreateTradeRequest(BaseModel):
    meter_id: str = Field(min_length=1)
    producer_id: str = Field(min_length=1)
    consumer_id: str = Field(min_length=1)
    expected_kwh: Decimal = Field(gt=0)
    invoice_expiry_seconds: int = Field(default=900, ge=60, le=86400)


class MeterDeliveryRequest(BaseModel):
    reading_id: str = Field(min_length=1)
    trade_id: str = Field(min_length=1)
    meter_id: str = Field(min_length=1)
    delivered_kwh: Decimal = Field(gt=0)


class Trade(BaseModel):
    id: str
    meter_id: str
    producer_id: str
    consumer_id: str
    expected_kwh: Decimal
    delivered_kwh: Decimal = Decimal("0")
    amount_sats: int
    payment_hash: str
    payment_request: str
    status: TradeStatus
    created_at: datetime
    settled_at: datetime | None = None


trades: dict[str, Trade] = {}
processed_readings: set[str] = set()
state_lock = asyncio.Lock()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def trade_data(trade: Trade) -> dict[str, Any]:
    return jsonable_encoder(trade)


def get_trade_or_404(trade_id: str) -> Trade:
    trade = trades.get(trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


def verify_meter_signature(payload: MeterDeliveryRequest, signature: str | None) -> None:
    if not METER_HMAC_SECRET:
        return
    if not signature:
        raise HTTPException(status_code=401, detail="Missing X-Meter-Signature")

    signed_message = (
        f"{payload.meter_id}:{payload.reading_id}:"
        f"{payload.trade_id}:{payload.delivered_kwh}"
    )
    expected = hmac.new(
        METER_HMAC_SECRET.encode(),
        signed_message.encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid meter signature")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "lightning_mode": lightning.mode}


@app.post("/trades", response_model=Trade, status_code=status.HTTP_201_CREATED)
async def create_trade(payload: CreateTradeRequest) -> Trade:
    amount_sats = int((payload.expected_kwh * SATS_PER_KWH).to_integral_value(
        rounding=ROUND_CEILING
    ))
    trade_id = str(uuid4())

    try:
        invoice = await lightning.create_hold_invoice(
            amount_sats=amount_sats,
            memo=f"SolarSats delivery {trade_id}",
            expiry_seconds=payload.invoice_expiry_seconds,
        )
    except LightningError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    trade = Trade(
        id=trade_id,
        meter_id=payload.meter_id,
        producer_id=payload.producer_id,
        consumer_id=payload.consumer_id,
        expected_kwh=payload.expected_kwh,
        amount_sats=invoice.amount_sats,
        payment_hash=invoice.payment_hash,
        payment_request=invoice.payment_request,
        status=TradeStatus.OPEN,
        created_at=utc_now(),
    )
    async with state_lock:
        trades[trade.id] = trade

    await manager.broadcast("trade.created", trade_data(trade))
    return trade


@app.post("/trades/{trade_id}/fund", response_model=Trade)
async def fund_trade(trade_id: str) -> Trade:
    async with state_lock:
        trade = get_trade_or_404(trade_id)
        if trade.status != TradeStatus.OPEN:
            raise HTTPException(status_code=409, detail="Only an open trade can be funded")
        try:
            await lightning.fund_hold_invoice(trade.payment_hash, trade.payment_request)
        except LightningError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        trade.status = TradeStatus.FUNDED

    await manager.broadcast("trade.funded", trade_data(trade))
    return trade


@app.post("/meter/delivery", response_model=Trade)
async def confirm_delivery(
    payload: MeterDeliveryRequest,
    x_meter_signature: str | None = Header(default=None),
) -> Trade:
    verify_meter_signature(payload, x_meter_signature)
    reading_key = f"{payload.meter_id}:{payload.reading_id}"

    async with state_lock:
        if reading_key in processed_readings:
            raise HTTPException(status_code=409, detail="Meter reading already processed")

        trade = get_trade_or_404(payload.trade_id)
        if trade.meter_id != payload.meter_id:
            raise HTTPException(status_code=403, detail="Meter is not paired with this trade")
        if trade.status != TradeStatus.FUNDED:
            raise HTTPException(status_code=409, detail="Trade must be funded before delivery")
        if payload.delivered_kwh < trade.expected_kwh:
            raise HTTPException(
                status_code=422,
                detail="Delivered energy is below the agreed amount",
            )

        try:
            await lightning.settle_hold_invoice(trade.payment_hash)
        except LightningError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        processed_readings.add(reading_key)
        trade.delivered_kwh = payload.delivered_kwh
        trade.status = TradeStatus.SETTLED
        trade.settled_at = utc_now()

    await manager.broadcast("trade.settled", trade_data(trade))
    return trade


@app.post("/trades/{trade_id}/cancel", response_model=Trade)
async def cancel_trade(trade_id: str) -> Trade:
    async with state_lock:
        trade = get_trade_or_404(trade_id)
        if trade.status not in {TradeStatus.OPEN, TradeStatus.FUNDED}:
            raise HTTPException(status_code=409, detail="Trade cannot be cancelled")
        try:
            await lightning.cancel_hold_invoice(trade.payment_hash)
        except LightningError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        trade.status = TradeStatus.CANCELED

    await manager.broadcast("trade.canceled", trade_data(trade))
    return trade


@app.get("/trades", response_model=list[Trade])
async def list_trades() -> list[Trade]:
    return list(trades.values())


@app.get("/trades/{trade_id}", response_model=Trade)
async def get_trade(trade_id: str) -> Trade:
    return get_trade_or_404(trade_id)


@app.websocket("/ws")
async def websocket_updates(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        await websocket.send_json(
            {"event": "connected", "data": {"message": "SolarSats live updates"}}
        )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
