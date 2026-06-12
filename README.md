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

### Frontend

From the repository root, install the Flutter dependencies:

```bash
cd Frontend/solar_sats
flutter pub get
```

Start the Flutter web app:

```bash
flutter run -d chrome
```

To run on another configured device, list the available targets with
`flutter devices`, then run:

```bash
flutter run -d <device-id>
```
