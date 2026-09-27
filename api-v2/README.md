# api-v2 — Bharat Weather Intelligence V2 intelligence API

Separate FastAPI service (`/api/v2`). Reads CORE only through CORE's public `/api/v1` over
HTTP (`app/core_client.py`); imports no CORE code and changes nothing in CORE.

| Endpoint | Purpose |
|---|---|
| `/api/v2/events?lat&lon&name` | CORE risks at Watch+ as events; official alerts separate; what-should-you-know priority |
| `/api/v2/evidence?lat&lon&name&risk` | Nine-section evidence (DATA → RULE → RESULT) for one risk |
| `/api/v2/region/india/risks` | District counts (heat/cold/rain/wind) + official-alert districts, reconciled with CORE `/region/state` |
| `/api/v2/health` | Service and CORE status |

Method: `../docs/EVENTS_AND_EVIDENCE.md`. Wording and data mappings (no thresholds):
`app/catalogue.py`.

```bash
pip install -r requirements-dev.txt
python -m pytest -q                 # offline tests with captured CORE responses (tests/fixtures)
uvicorn app.main:app --port 8702
```

Deployed as its own Vercel project (root directory `api-v2`, entry `index.py`, region bom1).
