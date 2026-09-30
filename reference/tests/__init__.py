"""Offline test helpers for D2: synthetic ERA5-like GRIB files (ecCodes), a fake CDS service and a fake GitHub.

The synthetic GRIB files reproduce the structure of CDS ERA5 total precipitation: GRIB1, class ea / stream oper,
dataType fc with base times 06 and 18 UTC and hourly accumulation steps 1-12, regular 0.25° grid, 16-bit simple
packing, local expver key. No real ERA5 data is used.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
from datetime import datetime, timedelta

import numpy as np

HERE = pathlib.Path(__file__).resolve().parents[1]
ROOT = HERE.parent
for p in (str(HERE), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

import era5_common as C  # noqa: E402
from era5_cds import CDSHTTPError, CDSTransportError  # noqa: E402

KEY = "k3y-7f2c9e10-SECRET-cds-token-0000"       # fake CDS key; must never appear in any output


def base_and_step(t: datetime) -> tuple[datetime, int]:
    """ERA5 accumulations: validity 07..18Z from the 06Z base (steps 1..12), 19..06Z from the 18Z base."""
    h = t.hour
    if 7 <= h <= 18:
        return t.replace(hour=6), h - 6
    if h >= 19:
        return t.replace(hour=18), h - 18
    return (t - timedelta(days=1)).replace(hour=18), h + 6


def default_value(t: datetime, lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
    """Deterministic, spatially varying hourly precipitation in metres (0 .. ~1.3 mm per hour)."""
    la, lo = np.meshgrid(lats, lons, indexing="ij")
    k = (t - datetime(2000, 1, 1, tzinfo=t.tzinfo)).total_seconds() / 3600.0
    v = 0.0006 * (1 + np.sin(k / 5.0 + la / 3.0) * np.cos(lo / 4.0))
    return v.ravel()


def write_grib(path: pathlib.Path, request: dict, *, value_fn=default_value, expver=None, drop=(), duplicate=(),
               missing=None, short_name="tp", area=None, no_local=False, perturb=None) -> pathlib.Path:
    """Write one synthetic GRIB file answering `request`.

    expver: callable(stamp) -> str (default '0001'); drop / duplicate: stamps to omit / repeat;
    missing: {stamp: [flat indices]} set to GRIB missing; area: override the grid; no_local: omit the local section
    (no expver key at all); perturb: callable(stamp, values) -> values (applied before packing)."""
    import eccodes as ec
    n, w, s, e = request["area"] if area is None else area
    lats = n - 0.25 * np.arange(int(round((n - s) / 0.25)) + 1)
    lons = w + 0.25 * np.arange(int(round((e - w) / 0.25)) + 1)
    stamps = [t for t in C.expected_stamps(request) if t not in set(drop)] + list(duplicate)
    tmpl = ec.codes_grib_new_from_samples("regular_ll_sfc_grib1")
    ec.codes_set(tmpl, "centre", "kwbc" if no_local else "ecmf")     # non-ECMWF centre: no local section, no expver
    if not no_local:
        ec.codes_set(tmpl, "setLocalDefinition", 1)
        ec.codes_set(tmpl, "localDefinitionNumber", 1)
        for k, v in (("marsClass", "ea"), ("marsType", "fc"), ("marsStream", "oper")):
            ec.codes_set(tmpl, k, v)
    ec.codes_set(tmpl, "table2Version", 128)
    ec.codes_set(tmpl, "indicatorOfParameter", 228 if short_name == "tp" else 167)
    for k, v in (("Ni", len(lons)), ("Nj", len(lats)), ("latitudeOfFirstGridPointInDegrees", float(n)),
                 ("longitudeOfFirstGridPointInDegrees", float(w)), ("latitudeOfLastGridPointInDegrees", float(s)),
                 ("longitudeOfLastGridPointInDegrees", float(e)), ("iDirectionIncrementInDegrees", 0.25),
                 ("jDirectionIncrementInDegrees", 0.25), ("bitsPerValue", 16), ("stepType", "accum")):
        ec.codes_set(tmpl, k, v)
    with open(path, "wb") as f:
        for t in stamps:
            h = ec.codes_clone(tmpl)
            base, step = base_and_step(t)
            ec.codes_set(h, "dataDate", int(base.strftime("%Y%m%d")))
            ec.codes_set(h, "dataTime", base.hour * 100)
            ec.codes_set(h, "startStep", step - 1)
            ec.codes_set(h, "endStep", step)
            if not no_local:
                ec.codes_set(h, "experimentVersionNumber", (expver or (lambda _t: "0001"))(t))
            v = np.asarray(value_fn(t, lats, lons), dtype=np.float64)
            if perturb is not None:
                v = perturb(t, v.copy())
            if missing and t in missing:
                ec.codes_set(h, "missingValue", 9999)
                ec.codes_set(h, "bitmapPresent", 1)
                v = v.copy()
                v[list(missing[t])] = 9999
            ec.codes_set_values(h, v)
            f.write(ec.codes_get_message(h))
            ec.codes_release(h)
    ec.codes_release(tmpl)
    return path


def flat_index(lat: float, lon: float, area=None) -> int:
    n, w, s, e = C.AREA if area is None else area
    ni = int(round((e - w) / 0.25)) + 1
    return int(round((n - lat) / 0.25)) * ni + int(round((lon - w) / 0.25))


# ---------------------------------------------------------------- fake CDS
class FakeCDS:
    """In-memory CDS with fault injection. Records every call; never touches the network."""

    def __init__(self, tmp: pathlib.Path, *, grib_kwargs=None):
        self.tmp = pathlib.Path(tmp)
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.jobs = {}                      # rid -> {"request":..., "polls": int}
        self.calls = []                     # ("submit"|"status"|"download", rid or sha)
        self.submit_errors = []             # exceptions raised by successive submit calls
        self.status_script = {}             # role -> list of statuses / exceptions returned before "successful"
        self.download_script = {}           # role -> list of exceptions / "truncate" before a good download
        self.grib_kwargs = grib_kwargs or {}  # role or (retrieval_no, role) -> write_grib kwargs
        self.observer = None                # callable(event, rid) run at submit time (e.g. check the ledger)
        self._n = 0
        self._cache = {}

    def _role(self, request):
        return "boundary" if len(request["time"]) == 5 else "month"

    def submit(self, request):
        self.calls.append(("submit", C.request_sha256(request)))
        if self.observer:
            self.observer("submit", request)
        if self.submit_errors:
            raise self.submit_errors.pop(0)
        self._n += 1
        rid = f"00000000-0000-0000-0000-{self._n:012d}"
        role = self._role(request)
        nth = sum(1 for j in self.jobs.values() if self._role(j["request"]) == role) + 1
        self.jobs[rid] = {"request": json.loads(json.dumps(request)), "role": role, "nth": nth,
                          "status": list(self.status_script.get(role, [])),
                          "download": list(self.download_script.get(role, []))}
        return rid

    def status(self, rid):
        self.calls.append(("status", rid))
        j = self.jobs[rid]
        if j["status"]:
            x = j["status"].pop(0)
            if isinstance(x, Exception):
                raise x
            return x
        return "successful"

    def _bytes(self, j) -> bytes:
        kw = self.grib_kwargs.get((j["nth"], j["role"]), self.grib_kwargs.get(j["role"], {}))
        key = (C.request_sha256(j["request"]), j["role"], j["nth"], repr(sorted(kw)))
        if key not in self._cache:
            p = self.tmp / f"gen_{len(self._cache)}.grib"
            write_grib(p, j["request"], **kw)
            self._cache[key] = p.read_bytes()
        return self._cache[key]

    def download(self, rid, target):
        self.calls.append(("download", rid))
        j = self.jobs[rid]
        data = self._bytes(j)
        if j["download"]:
            x = j["download"].pop(0)
            if isinstance(x, Exception):
                raise x
            if x == "truncate":
                pathlib.Path(target).write_bytes(data[: len(data) // 2])     # connection dropped mid-transfer
                return {"announced_bytes": len(data)}
            if x == "garbage":
                pathlib.Path(target).write_bytes(b"GRIB" + b"\x00" * 64)     # right size claim, undecodable body
                return {"announced_bytes": 68}
        pathlib.Path(target).write_bytes(data)
        return {"announced_bytes": len(data)}

    def submits(self) -> int:
        return sum(1 for c in self.calls if c[0] == "submit")


def transport(msg="connection reset"):
    return CDSTransportError(f"ConnectionError: {msg} (key {KEY})")


def http(status, msg="error"):
    return CDSHTTPError(status, f"{status} Client Error: {msg} PRIVATE-TOKEN: {KEY}")


# ---------------------------------------------------------------- fake GitHub (immutable after publication)
class FakeGH:
    def __init__(self):
        self.rel = {}
        self.fail_upload = set()
        self.corrupt_on_upload = set()
        self.deleted = []

    def state(self, tag):
        r = self.rel.get(tag)
        return "none" if r is None else ("draft" if r["draft"] else "published")

    def create_draft(self, tag, title, notes):
        assert tag not in self.rel
        self.rel[tag] = {"draft": True, "assets": {}, "notes": notes}

    def list_assets(self, tag):
        return sorted(self.rel[tag]["assets"])

    def download(self, tag, name, dest):
        (dest / name).write_bytes(self.rel[tag]["assets"][name])
        return dest / name

    def upload(self, tag, path):
        r = self.rel[tag]
        if not r["draft"]:
            raise RuntimeError("HTTP 422: release is immutable")
        if path.name in r["assets"]:
            raise RuntimeError("HTTP 422: ReleaseAsset.name already exists")
        if path.name in self.fail_upload:
            raise RuntimeError("HTTP 502: upload failed")
        data = path.read_bytes()
        r["assets"][path.name] = data + b"X" if path.name in self.corrupt_on_upload else data

    def delete_asset(self, tag, name):
        if not self.rel[tag]["draft"]:
            raise RuntimeError("HTTP 422: release is immutable")
        del self.rel[tag]["assets"][name]

    def publish(self, tag):
        self.rel[tag]["draft"] = False

    def delete_draft(self, tag):
        if self.state(tag) == "draft":
            del self.rel[tag]
            self.deleted.append(tag)

    def url(self, tag):
        return f"https://example.invalid/releases/{tag}"

    def verify_published(self, tag, stage, target_kind):
        """Same checks as archive/verify_release.py, against the in-memory release."""
        man = json.loads(next(stage.glob("manifest_*.json")).read_text())
        assets = self.rel[tag]["assets"]
        ok = all(hashlib.sha256(assets[f["name"]]).hexdigest() == f["sha256"] for f in man["files"])
        target = next(f["name"] for f in man["files"] if f["kind"] == target_kind)
        attempts = {}
        probe = stage.parent / "immutability_probe.txt"
        probe.write_text("must be rejected\n")
        for k, fn in (("add_new_asset", lambda: self.upload(tag, probe)),
                      ("delete_asset", lambda: self.delete_asset(tag, target))):
            try:
                fn()
                attempts[k] = {"rejected": False}
            except RuntimeError:
                attempts[k] = {"rejected": True}
        ok &= all(a["rejected"] for a in attempts.values())
        return ok, {"immutability": {"github_immutable_flag": True, **attempts}, "ok": ok}


def scan_for_secret(*roots) -> list[str]:
    hits = []
    for root in roots:
        root = pathlib.Path(root)
        for p in (root.rglob("*") if root.is_dir() else [root]):
            if p.is_file() and KEY.encode() in p.read_bytes():
                hits.append(str(p))
    return hits
