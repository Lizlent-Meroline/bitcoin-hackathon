"""Lightning HODL invoice operations for SolarSats.

Mock mode is enabled by default so the hackathon API can run without an LND
node. Set LIGHTNING_MODE=lnd and the LND_* environment variables to use LND's
REST API.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import secrets
from dataclasses import dataclass
from typing import Any


class LightningError(RuntimeError):
    """Raised when a Lightning operation cannot be completed."""


@dataclass(frozen=True)
class HoldInvoice:
    payment_hash: str
    payment_request: str
    amount_sats: int


class LightningService:
    def __init__(self) -> None:
        self.mode = os.getenv("LIGHTNING_MODE", "mock").lower()
        self.lnd_rest_url = os.getenv("LND_REST_URL", "https://127.0.0.1:8080").rstrip("/")
        self.macaroon_path = os.getenv("LND_MACAROON_PATH")
        self.tls_cert_path = os.getenv("LND_TLS_CERT_PATH")
        self.consumer_lnd_rest_url = os.getenv(
            "CONSUMER_LND_REST_URL", self.lnd_rest_url
        ).rstrip("/")
        self.consumer_macaroon_path = os.getenv(
            "CONSUMER_LND_MACAROON_PATH", self.macaroon_path
        )
        self.consumer_tls_cert_path = os.getenv(
            "CONSUMER_LND_TLS_CERT_PATH", self.tls_cert_path
        )
        self._preimages: dict[str, bytes] = {}
        self._mock_states: dict[str, str] = {}
        self._payment_tasks: set[asyncio.Task[None]] = set()

        if self.mode not in {"mock", "lnd"}:
            raise ValueError("LIGHTNING_MODE must be either 'mock' or 'lnd'")

    async def create_hold_invoice(
        self, amount_sats: int, memo: str, expiry_seconds: int = 900
    ) -> HoldInvoice:
        if amount_sats <= 0:
            raise LightningError("Invoice amount must be greater than zero")

        preimage = secrets.token_bytes(32)
        payment_hash_bytes = hashlib.sha256(preimage).digest()
        payment_hash = payment_hash_bytes.hex()
        self._preimages[payment_hash] = preimage

        if self.mode == "mock":
            payment_request = f"lnmock-{amount_sats}-{payment_hash}"
            self._mock_states[payment_hash] = "OPEN"
        else:
            try:
                response = await self._request(
                    "POST",
                    "/v2/invoices/hodl",
                    {
                        "hash": base64.b64encode(payment_hash_bytes).decode(),
                        "value": str(amount_sats),
                        "memo": memo,
                        "expiry": str(expiry_seconds),
                    },
                )
            except Exception:
                self._preimages.pop(payment_hash, None)
                raise
            payment_request = response.get("payment_request", "")
            if not payment_request:
                self._preimages.pop(payment_hash, None)
                raise LightningError("LND did not return a payment request")

        return HoldInvoice(
            payment_hash=payment_hash,
            payment_request=payment_request,
            amount_sats=amount_sats,
        )

    async def fund_hold_invoice(self, payment_hash: str, payment_request: str) -> None:
        self._require_known_hash(payment_hash)

        if self.mode == "mock":
            if self._mock_states[payment_hash] != "OPEN":
                raise LightningError("HODL invoice is not open")
            self._mock_states[payment_hash] = "ACCEPTED"
            return

        task = asyncio.create_task(self._send_payment_stream(payment_request))
        self._payment_tasks.add(task)
        task.add_done_callback(self._payment_finished)

    async def settle_hold_invoice(self, payment_hash: str) -> None:
        preimage = self._require_known_hash(payment_hash)

        if self.mode == "mock":
            if self._mock_states[payment_hash] != "ACCEPTED":
                raise LightningError("HODL invoice must be funded before settlement")
            self._mock_states[payment_hash] = "SETTLED"
        else:
            await self._request(
                "POST",
                "/v2/invoices/settle",
                {"preimage": base64.b64encode(preimage).decode()},
            )

        self._preimages.pop(payment_hash, None)

    async def cancel_hold_invoice(self, payment_hash: str) -> None:
        self._require_known_hash(payment_hash)

        if self.mode == "mock":
            if self._mock_states[payment_hash] == "SETTLED":
                raise LightningError("A settled HODL invoice cannot be cancelled")
            self._mock_states[payment_hash] = "CANCELED"
        else:
            await self._request(
                "POST",
                "/v2/invoices/cancel",
                {"payment_hash": base64.b64encode(bytes.fromhex(payment_hash)).decode()},
            )

        self._preimages.pop(payment_hash, None)

    def _require_known_hash(self, payment_hash: str) -> bytes:
        try:
            return self._preimages[payment_hash]
        except KeyError as exc:
            raise LightningError("Unknown or already finalized payment hash") from exc

    async def _send_payment_stream(self, payment_request: str) -> None:
        try:
            import httpx
        except ImportError as exc:
            raise LightningError("Install httpx to use LIGHTNING_MODE=lnd") from exc

        async with httpx.AsyncClient(
            verify=self.consumer_tls_cert_path or True,
            headers=self._headers(self.consumer_macaroon_path),
            timeout=None,
        ) as client:
            async with client.stream(
                "POST",
                f"{self.consumer_lnd_rest_url}/v2/router/send",
                json={"payment_request": payment_request, "timeout_seconds": 300},
            ) as response:
                if response.is_error:
                    raise LightningError(await response.aread())
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    update = json.loads(line)
                    result = update.get("result", update)
                    if result.get("status") == "FAILED":
                        raise LightningError(
                            result.get("failure_reason", "Lightning payment failed")
                        )

    async def _request(self, method: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            import httpx
        except ImportError as exc:
            raise LightningError("Install httpx to use LIGHTNING_MODE=lnd") from exc

        async with httpx.AsyncClient(
            verify=self.tls_cert_path or True,
            headers=self._headers(self.macaroon_path),
            timeout=30,
        ) as client:
            response = await client.request(
                method, f"{self.lnd_rest_url}{path}", json=payload
            )
            if response.is_error:
                raise LightningError(f"LND returned {response.status_code}: {response.text}")
            return response.json()

    def _headers(self, macaroon_path: str | None) -> dict[str, str]:
        if not macaroon_path:
            raise LightningError("LND_MACAROON_PATH is required in lnd mode")
        with open(macaroon_path, "rb") as macaroon_file:
            macaroon = macaroon_file.read().hex()
        return {"Grpc-Metadata-macaroon": macaroon}

    def _payment_finished(self, task: asyncio.Task[None]) -> None:
        self._payment_tasks.discard(task)
        try:
            task.exception()
        except asyncio.CancelledError:
            pass


lightning = LightningService()
