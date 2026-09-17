# Local & Docker Operation

## Local Python (development and troubleshooting)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

python scripts/seed_demo.py      # initializes the SQLite schema, validates all scenario files
uvicorn app.main:app --reload      # API: http://localhost:8000
streamlit run demo/streamlit_app.py  # Demo UI: http://localhost:8501 (separate terminal)
```

`scripts/seed_demo.py` is idempotent — it only creates tables if they don't already exist and
validates scenario JSON files; it never writes scenario data into the database (scenarios are
always read fresh from `data/scenarios/*.json`). Safe to re-run at any time.

`scripts/reset_demo.py` drops and recreates every table, clearing all audit events, decisions,
gate evaluations, and close-out reports — use it to return to a clean state before a fresh
walkthrough:

```bash
python scripts/reset_demo.py
```

## Docker (mandatory-supported alternative)

```bash
docker compose up --build
```

This builds one image (`Dockerfile`) and runs it as two services (`docker-compose.yml`):

| Service | Container | Port | Command |
|---|---|---|---|
| `api` | `copilot-api` | 8000 | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| `demo` | `copilot-demo` | 8501 | `streamlit run demo/streamlit_app.py` |

### Build failure on TLS-inspecting networks

Some antivirus "web protection" features (Norton, Kaspersky, etc.) and corporate proxies
intercept outbound TLS and re-sign it with a local root certificate. Windows trusts that root
automatically, but a fresh Docker Linux build context does not, so `pip install` inside the build
can fail with `SSL: CERTIFICATE_VERIFY_FAILED` even though the same install works fine on the
host. This is a property of the local network, not of the Dockerfile or the pinned dependencies.

Fix (does **not** weaken or bypass certificate verification — it adds the real root of trust this
network already uses):

```powershell
powershell -File scripts/export_local_ca_cert.ps1
docker compose up --build
```

The script copies the intercepting root certificate into `docker/extra-ca-certs/` (gitignored —
it is a public root certificate, not a secret, but it is machine-specific and never committed).
The Dockerfile trusts anything placed there in addition to the standard public CA bundle; on a
network without TLS inspection, the directory stays empty and this is a no-op.

- SQLite data persists in a named volume (`copilot-data`) mounted at `/app/data`, so restarting
  the containers does not lose audit history.
- `demo` talks to `api` over the Docker network (`API_BASE_URL=http://api:8000`) and waits for
  the API's healthcheck (`GET /health`) before starting.
- `LLM_MODE`, the `OPENAI_COMPATIBLE_*` variables, and `LOG_LEVEL` are all pass-through
  environment variables (default `LLM_MODE=mock`) — set them in a `.env` file or your shell before
  running `docker compose up` to enable the opt-in LLM adapter.

```bash
docker compose down            # stop and remove containers (keeps the named volume)
docker compose down -v          # also remove the persisted SQLite volume
```

## Local URLs (either run method)

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Streamlit demo | http://localhost:8501 |
| Prometheus metrics | http://localhost:8000/metrics |

## Environment Variables

See `.env.example` for the full list with defaults. Nothing is required for default (offline,
mock-LLM) operation — every variable has a safe default.
