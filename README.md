# SolarSats

## Prerequisites

- Python and `pip`
- [Flutter SDK](https://docs.flutter.dev/get-started/install) with a supported
  browser or another configured Flutter device

## Run Locally

Run the backend and frontend in separate terminals.

### Backend

From the repository root, install the FastAPI backend dependencies:

```bash
python -m pip install -r backend/requirements.txt
```

Start the backend development server:

```bash
python -m uvicorn backend.main:app --reload
```

The API runs at `http://127.0.0.1:8000`. Open the interactive API
documentation at `http://127.0.0.1:8000/docs` or check the health endpoint at
`http://127.0.0.1:8000/health`.

The backend uses its built-in mock Lightning implementation by default, so no
Lightning node configuration is required for local development.

### Run With A Local Lightning Network

On Linux or WSL, run the included setup script from the repository root:

```bash
bash backend/start-lightning-fix.sh
```

The script starts Bitcoin Core regtest, creates producer Alice and consumer Bob
LND nodes, gives Bob outbound channel liquidity, and writes
`backend/.env.lightning` for the backend. Start the backend from the same
Linux/WSL environment so it can access the generated TLS certificates and
macaroons:

```bash
python -m uvicorn backend.main:app --reload
```

Check `http://127.0.0.1:8000/health` and confirm `lightning_mode` is `lnd`.
In this mode Alice creates the HODL invoice, Bob pays it through Lightning, and
the meter delivery endpoint releases the held payment to Alice. Calling
`POST /demo/run` performs this flow against the local Lightning nodes.

### Run The Payment And Energy Demo

With the backend running, open `http://127.0.0.1:8000/docs` and call:

```text
POST /demo/run
```

The demo creates a 2 kWh trade from Alice to Bob, moves Bob's sats into a
Lightning HODL invoice, confirms delivery from Alice's meter, transfers the
energy to Bob, and releases the sats to Alice. It uses the mock implementation
by default or the local LND nodes when `backend/.env.lightning` exists. Inspect
the resulting account balances, trade, and event ledger with:

```text
GET /demo/state
```

## Flutter Web Frontend

From the repository root, install the Flutter dependencies:

```bash
cd Frontend/solar_sats
flutter pub get
flutter pub add http web_socket_channel
```

Start the web app on a fixed development port:

```bash
flutter run -d chrome --web-port 3000
```

Use these backend URLs in the Flutter web app:

```text
HTTP API:  http://127.0.0.1:8000
WebSocket: ws://127.0.0.1:8000/ws
```

The browser frontend currently requires CORS to be enabled on the backend for
`http://localhost:3000` and `http://127.0.0.1:3000`, or a development proxy
that serves both applications from the same origin.

Keep the API base URL configurable instead of hard-coding it throughout the
Flutter app. A recommended web run command is:

```bash
flutter run -d chrome --web-port 3000 \
  --dart-define=API_BASE_URL=http://127.0.0.1:8000 \
  --dart-define=WS_BASE_URL=ws://127.0.0.1:8000/ws
```

### Frontend Responsibilities

The frontend should:

- Display account balances, available energy, received energy, trades, and the
  event ledger from `GET /demo/state`.
- Create a trade using `POST /trades`.
- Let the consumer fund the Lightning HODL invoice using
  `POST /trades/{trade_id}/fund`.
- Let either participant cancel an open or funded trade using
  `POST /trades/{trade_id}/cancel`.
- Subscribe to `ws://127.0.0.1:8000/ws` and update the UI from live events.

The frontend must **not**:

- Connect directly to LND or receive TLS certificates or macaroons.
- Mark electricity as delivered.
- Call `POST /meter/delivery`; that endpoint is reserved for the trusted smart
  meter or meter simulator.
- Assume a Lightning payment is complete while a trade is only `FUNDED`.

### Demo Accounts

After `POST /demo/reset`, the backend provides:

| Role | Account ID | Starting State |
| --- | --- | --- |
| Producer | `producer-alice` | 10 kWh available, 0 sats |
| Consumer | `consumer-bob` | 0 kWh received, 10,000 sats |
| Producer meter | `meter-alice-01` | Confirms Alice's delivery |

Use these IDs exactly when building the first web demonstration.

### Trade Flow

1. Reset and load the initial state:

   ```http
   POST /demo/reset
   GET /demo/state
   ```

2. Create a trade:

   ```http
   POST /trades
   Content-Type: application/json

   {
     "meter_id": "meter-alice-01",
     "producer_id": "producer-alice",
     "consumer_id": "consumer-bob",
     "expected_kwh": "2",
     "invoice_expiry_seconds": 900
   }
   ```

   Save the returned `id`. The trade is now `OPEN`, and Alice's energy is
   reserved.

3. Fund the trade:

   ```http
   POST /trades/{trade_id}/fund
   ```

   The backend makes Bob pay Alice's HODL invoice through Lightning. Only show
   the trade as funded after this request returns `200` with status `FUNDED`.

4. Wait for the trusted meter to confirm delivery. After settlement, the
   frontend receives a `trade.settled` WebSocket event and the trade status
   becomes `SETTLED`.

For a one-button demonstration, call `POST /demo/run`. It performs the complete
trade, Lightning payment, meter delivery, and settlement flow.

### Trade Statuses

| Status | Meaning |
| --- | --- |
| `OPEN` | Energy is reserved and the HODL invoice exists. |
| `FUNDED` | Bob's Lightning payment is held; electricity may now flow. |
| `SETTLED` | Delivery was confirmed and payment was released to Alice. |
| `CANCELED` | Reserved energy was released and held sats were refunded. |

### Backend Responses

`GET /demo/state` returns:

```json
{
  "accounts": [],
  "trades": [],
  "ledger": []
}
```

Energy values use decimal precision and may arrive as JSON strings such as
`"2"`. Parse them before performing calculations in Dart. Treat backend error
responses as:

```json
{
  "detail": "Human-readable error message"
}
```

Display the `detail` message when an API request returns a non-2xx status.

The current backend has no user authentication and stores demo accounts and
trades in memory. Restarting the backend clears the current state.

### WebSocket Events

Every WebSocket message uses this envelope:

```json
{
  "event": "trade.funded",
  "data": {}
}
```

Handle these events:

```text
connected
demo.reset
trade.created
trade.funded
trade.settled
trade.canceled
```

For trade events, `data` contains the updated trade. After `demo.reset`, fetch
`GET /demo/state` again because its `data` contains the complete demo state.
