#!/usr/bin/env bash
# One-off: preserve the M0 monthly release as an immutable, clearly marked legacy release.
# The original M0 release (archive-2026-09) is kept unchanged except for a LEGACY note in its description.
set -euo pipefail
SRC=archive-2026-09; TAG=archive-legacy-m0-2026-09; D="$RUNNER_TEMP/legacy"; mkdir -p "$D"
if gh release view "$TAG" --json isDraft -q .isDraft 2>/dev/null | grep -q false; then echo "$TAG already exists"; exit 0; fi
gh release download "$SRC" -D "$D"
python - "$D" <<'PY'
import json, pathlib, sys, hashlib, datetime
d = pathlib.Path(sys.argv[1])
files = []
for p in sorted(d.iterdir()):
    files.append({"name": p.name, "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
man = {
  "schema_version": 0, "kind": "legacy_m0", "source_release": "archive-2026-09",
  "preserved_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
  "provenance_complete": False, "run_time_known": False,
  "files": files,
  "provenance_notes": [
    "points_2026-09-27.json: Open-Meteo per-model daily forecasts; the model run (initialisation) times were NOT recorded -> run_time_known = false. Not usable for lead-time verification.",
    "e2s_gfs_daily_2026092706.nc: re-uploaded with --clobber at 2026-09-27T16:15Z after the lead_day unit fix (seconds -> days); the first upload (16:03Z) was not retained. Earth2Studio issue time 2026-09-27T06:00Z is recorded in the file.",
    "The M0 release was appendable and mutable; these files are preserved here immutably as they stood on the preservation date."
  ]}
(d / "legacy_manifest_m0_2026-09.json").write_text(json.dumps(man, indent=1) + "\n")
PY
gh release create "$TAG" --draft --latest=false --title "LEGACY M0 archive (Sep 2026) — provenance incomplete" \
  --notes "Immutable copy of the M0 monthly archive files. Provenance is INCOMPLETE: Open-Meteo run times were not recorded (run_time_known=false) and the Earth2Studio file was overwritten once during M0. See legacy_manifest_m0_2026-09.json. Not for lead-time verification." \
  "$D"/*
gh release edit "$TAG" --draft=false --latest=false
gh release edit "$SRC" --title "LEGACY M0 archive Sep 2026 (mutable, provenance incomplete)" \
  --notes "LEGACY (M0). Mutable monthly release, superseded on $(date -u +%F) by immutable daily releases (archive-daily-YYYY-MM-DD). Open-Meteo run times were not recorded; the Earth2Studio file was overwritten once. An immutable copy is in $TAG. Do not add files."
mkdir -p "$IDX/index/legacy" && cp "$D/legacy_manifest_m0_2026-09.json" "$IDX/index/legacy/"
cd "$IDX" && git add -A && git commit -qm "archive: preserve M0 legacy release as $TAG (provenance incomplete)" && git push -q origin archive-index
