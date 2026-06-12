# SolarSats

## Run The Backend

Install dependencies:

```bash
python -m pip install -r backend/requirements.txt
```

From the repository root:

```bash
python -m uvicorn backend.main:app --reload
```

From inside the `backend` directory:

```bash
python -m uvicorn main:app --reload
```

Open the interactive API documentation at `http://127.0.0.1:8000/docs`.
