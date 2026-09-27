# M2 acceptance test

Compares CORE `/api/v1` (truth) with V2's `/api/v2` and the V2 website for Ahmedabad (no event),
Shimla (several watches), Chennai and Guwahati (official alerts + system watches) and
Uttarkashi (official alerts + severe/alert/watch system events). Checks 1–10 of the M2 brief:
timestamps, severity, model agreement, official separation, evidence values vs CORE data,
district counts vs an independent recount of all 36 CORE state tables and vs the map,
no GFS double counting, no system item labelled official, no probability from agreement.

```bash
PLAYWRIGHT_CHROMIUM=/opt/pw-browsers/chromium node tools/m2-acceptance/acceptance.mjs \
  https://gnmcool.github.io/bharat-weather-intelligence-v2/ <api-v2>/api/v2 \
  https://bharat-weather-intelligence-brown.vercel.app/api/v1 --json m2.json
```
Read-only; exits 1 on any failure.
