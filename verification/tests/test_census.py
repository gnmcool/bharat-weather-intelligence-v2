"""Offline tests for the M4.4-A Gate 1 census (synthetic archive with planted answers; no network, no metrics)."""
from __future__ import annotations

import hashlib
import io
import json
import pathlib
import sys
from datetime import date, timedelta

import pandas as pd
import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import run_census  # noqa: E402
from common import MODELS, CensusError  # noqa: E402

# 12 synthetic points: 10 mainland (varied regions), 2 islands; two high-altitude
POINTS = [("P01", "Delhi", 200), ("P02", "Tamil Nadu", 80), ("P03", "Gujarat", 50), ("P04", "Bihar", 60),
          ("P05", "Kerala", 20), ("P06", "Rajasthan", 300), ("P07", "Assam", 70), ("P08", "Odisha", 30),
          ("P09", "Ladakh", 4983), ("P10", "Sikkim", 2470), ("P11", "Andaman and Nicobar Islands", 10),
          ("P12", "Lakshadweep", 5)]
STATIONS = {"P01": "VIDP", "P02": "VOTR"}           # matched METAR stations
METAR_F_DAYS = {2, 3}                                 # day-of-month with incomplete METAR coverage at P02 (F)
ISLANDS = {"P11", "P12"}                              # IMD: no cell within 30 km (G)
GFS_OUTAGE_DAYS = {1, 2, 3}                           # GFS precip (both windows) lead 2: source outage (C)
NA = "not provided by source: icon_global has no x at nominal lead 7 (M4.2 coverage matrix)"


def days_of(month: str):
    y, m = map(int, month.split("-"))
    d = date(y, m, 1)
    out = []
    while d.month == m:
        out.append(d)
        d += timedelta(days=1)
    return out


def build_month(month: str, extra_rows=None, feb_archive_start=False, d_row=False):
    rows, frows = [], []
    for pid, state, elev in POINTS:
        for model in MODELS:
            for lead in range(1, 8):
                for d in days_of(month):
                    for var in ("tmax", "tmin", "precip", "precip_0830", "gust_max"):
                        fa, fr, hp = True, None, 24
                        if model == "icon_global" and lead == 7:
                            fa, fr, hp = False, NA, 0
                        elif model == "gfs_global" and var in ("precip", "precip_0830") and lead == 2 and d.day in GFS_OUTAGE_DAYS:
                            fa, fr, hp = False, "source outage: 24 of 24 hours missing (retrieval succeeded; ...)", 0
                        elif feb_archive_start and model == "ecmwf_ifs025" and var == "tmax" and lead == 1 and d.day <= 2:
                            fa, fr, hp = False, "source hours missing: 24 of 24 (no interpolation, no substitution)", 0
                        elif d_row and model == "ecmwf_ifs025" and var == "tmin" and lead == 3 and d.day == 5:
                            fa, fr, hp = False, "source retrieval failed: synthetic", 0
                        fv = 30.0 if fa else None
                        frows.append({"model": model, "point_id": pid, "variable": var, "nominal_lead_day": lead,
                                      "valid_date_ist": d, "complete": fa, "reason": fr, "hours_present": hp})
                        refs = {"tmax": ["era5", "metar"], "tmin": ["era5", "metar"], "precip": ["era5"],
                                "precip_0830": ["imd_rf025", "era5"], "gust_max": ["era5", "metar"]}[var]
                        for ref in refs:
                            ra, rr, dist = True, None, 15.0
                            if ref == "metar" and var == "gust_max":
                                ra, rr, dist = False, "METAR reports a gust group only when gusts occur", None
                            elif ref == "metar" and pid not in STATIONS:
                                ra, rr, dist = False, "no METAR match: nearest station 60 km > 25 km", 60.0
                            elif ref == "metar" and pid == "P02" and d.day in METAR_F_DAYS:
                                ra, rr, dist = False, "incomplete reporting coverage: no report in IST 6-h block(s) 00-06h", 12.0
                            elif ref == "imd_rf025" and pid in ISLANDS:
                                ra, rr, dist = False, "no IMD cell within 30 km (nearest valid cell 369 km)", 369.0
                            rows.append({
                                "dataset": "matched_historical", "point_id": pid, "model": model, "run_time_known": False,
                                "nominal_lead_day": lead, "lead_basis": f"nominal previous_day{lead}", "valid_date_ist": d,
                                "variable": var, "window": "imd_0830" if var == "precip_0830" else "ist_day",
                                "unit": "x", "forecast_value": fv, "forecast_available": fa, "forecast_reason": fr,
                                "reference": ref, "reference_label": ref, "reference_variable": var,
                                "reference_value": (5.0 if d.day % 2 else 1.0) if ra else None,
                                "reference_available": ra, "reference_reason": rr, "ref_site_id": "s",
                                "ref_distance_km": dist, "ref_elev_diff_m": None})
    M = pd.DataFrame(rows + (extra_rows or []))
    F = pd.DataFrame(frows).drop_duplicates(["model", "point_id", "variable", "nominal_lead_day", "valid_date_ist"])
    pairing = {"pairs": [{"point_id": pid, "state": st, "point_elev_m": el, "paired": pid in STATIONS,
                          "station": STATIONS.get(pid, "XNEAR"), "distance_km": 8.0, "elev_diff_m": 10.0,
                          "reason_not_paired": None if pid in STATIONS else "nearest station 60 km > 25 km"}
                         for pid, st, el in POINTS]}
    return M, F, pairing


def pq_bytes(df):
    b = io.BytesIO()
    df.to_parquet(b, index=False)
    return b.getvalue()


class FakeSource:
    index_commit = "synthetic"

    def __init__(self):
        self.assets, self.recs, self.anns, self.rel = {}, {}, [], {}

    def add_month(self, month, M, F, pairing, dataset="historical_backfill"):
        tag = f"history-{month}"
        files = {f"matched_history-{month}.parquet": ("matched", pq_bytes(M)),
                 f"forecasts_history-{month}.parquet": ("forecasts", pq_bytes(F)),
                 f"metar_pairing_history-{month}.json": ("metar_pairing", json.dumps(pairing, default=str).encode())}
        man = {"dataset": dataset, "processing_version": "m4.3-2",
               "files": [{"kind": k, "name": n, "sha256": hashlib.sha256(b).hexdigest()} for n, (k, b) in files.items()]}
        mb = json.dumps(man).encode()
        self.assets[tag] = {n: b for n, (k, b) in files.items()}
        self.assets[tag][f"manifest_history-{month}.json"] = mb
        self.recs[month] = {"month": month, "tag": tag, "manifest_sha256": hashlib.sha256(mb).hexdigest()}
        self.rel[tag] = {"draft": False, "immutable": True, "id": 1}
        return tag

    def index_files(self, prefix):
        if prefix.endswith("index"):
            return {f"{prefix}/{m}.json": json.dumps(r).encode() for m, r in self.recs.items()}
        return {f"{prefix}/{a['id']}.json": json.dumps(a).encode() for a in self.anns}

    def release(self, tag):
        return self.rel[tag]

    def asset(self, tag, name):
        return self.assets[tag][name]


def cell(C, **kw):
    q = C
    for k, v in kw.items():
        q = q[q[k] == v]
    assert len(q) == 1, (kw, len(q))
    return q.iloc[0]


MONTH = "2025-07"
N_DAYS = 31


@pytest.fixture
def one_month(tmp_path):
    src = FakeSource()
    src.add_month(MONTH, *build_month(MONTH))
    rec = run_census.run(src, tmp_path / "out")
    C = pd.read_parquet(tmp_path / "out" / "census_cells.parquet")
    return src, rec, C, tmp_path / "out"


def test_known_answer_counts(one_month):
    _, rec, C, _ = one_month
    base = dict(comparison="single-model", geo_slice_type="pooled", geo_slice="all-points", season="all", stratum="all")
    c = cell(C, experiment="A1", model="ecmwf_ifs025", variable="tmax", lead=1, **base)
    assert (c.n_total, c.n_eligible, c.n_dates, c.n_points, c.n_excluded) == (12 * N_DAYS, 12 * N_DAYS, N_DAYS, 12, 0)
    c = cell(C, experiment="A1", model="icon_global", variable="tmax", lead=7, **base)
    assert c.n_eligible == 0 and c.excluded_A == 12 * N_DAYS and c.status == "insufficient sample"
    c = cell(C, experiment="A4", model="gfs_global", variable="precip", lead=2, **base)
    assert c.excluded_C == 12 * 3 and c.n_eligible == 12 * (N_DAYS - 3)       # outage never becomes an error or zero
    c = cell(C, experiment="A3", model="gfs_global", variable="precip_0830", lead=1, **base)
    assert c.excluded_G == 2 * N_DAYS and c.n_points == 10                      # islands: no IMD cell
    # totals: A1 = 12 pts x 3 models x 2 vars x 7 leads x 31 days
    assert rec["totals"]["A1"]["pairs"] == 12 * 3 * 2 * 7 * N_DAYS
    assert rec["totals"]["A1"]["eligible"] == 12 * 3 * 2 * 7 * N_DAYS - 12 * 2 * N_DAYS   # minus ICON lead 7
    assert rec["metrics_computed"] == "none"


def test_metar_station_level_only(one_month):
    _, _, C, out = one_month
    A2 = C[(C.experiment == "A2") & (C.comparison == "single-model")]
    assert set(A2.geo_slice_type) == {"station"} and set(A2.geo_slice) == {"VIDP", "VOTR"}   # never pooled
    c = cell(A2, model="gfs_global", variable="tmax", lead=1, geo_slice="VOTR", season="all", stratum="all")
    assert c.n_eligible == N_DAYS - 2 and c.excluded_F == 2
    assert c.status == "insufficient sample"                                   # < 90 station days
    X = pd.read_csv(out / "census_exclusions.csv")
    g = X[(X.experiment == "A2") & (X.reason == "G") & (X.model == "gfs_global") & (X.variable == "tmax") & (X.lead == 1)]
    assert int(g.n_excluded.sum()) == 10 * N_DAYS                                # unmatched points excluded as G


def test_gust_and_era5_0830_not_in_scope(one_month):
    _, _, C, _ = one_month
    assert "gust_max" not in set(C.variable)
    assert set(C[C.experiment == "A4"].variable) == {"precip"}                  # ERA5 rain = IST day only
    assert set(C[C.experiment == "A3"].window) == {"imd_0830"} and set(C[C.experiment == "A4"].window) == {"ist_day"}


def test_shared_data_eligibility(one_month):
    _, _, C, _ = one_month
    base = dict(geo_slice_type="pooled", geo_slice="all-points", season="all", stratum="all")
    c = cell(C, experiment="A4", comparison="shared-data:ecmwf_ifs025+gfs_global+icon_global", variable="precip", lead=2, **base)
    assert c.n_eligible == 12 * (N_DAYS - 3)                                    # GFS outage days drop from the intersection
    c = cell(C, experiment="A1", comparison="shared-data:ecmwf_ifs025+icon_global", variable="tmin", lead=7, **base)
    assert c.n_eligible == 0 and c.status == "not defined" and "ICON lead 7" in c.limitations
    c = cell(C, experiment="A1", comparison="shared-data:ecmwf_ifs025+gfs_global", variable="tmin", lead=7, **base)
    assert c.n_eligible == 12 * N_DAYS


def test_rainy_day_stratum_counts_only(one_month):
    _, _, C, _ = one_month
    c = cell(C, experiment="A3", comparison="single-model", model="ecmwf_ifs025", variable="precip_0830", lead=1,
             geo_slice_type="pooled", geo_slice="all-points", season="all", stratum="reference>=2.5mm")
    assert c.n_eligible == 10 * 16                                              # odd days (5 mm) at 10 IMD points
    bad = [col for col in C.columns if any(k in col.lower() for k in ("mae", "rmse", "bias", "pod", "far", "csi", "score"))]
    assert bad == []                                                            # no metric columns exist


def test_regions_islands_separate_and_floors(tmp_path):
    src = FakeSource()
    for m in ("2025-06", "2025-07", "2025-08"):
        src.add_month(m, *build_month(m))
    run_census.run(src, tmp_path / "o")
    C = pd.read_parquet(tmp_path / "o" / "census_cells.parquet")
    base = dict(experiment="A1", comparison="single-model", model="gfs_global", variable="tmax", lead=1, stratum="all")
    isl = cell(C, geo_slice_type="region", geo_slice="islands", season="all", **base)
    assert isl.n_points == 2 and isl.status == "insufficient sample"            # < 3 points: never published
    nw = cell(C, geo_slice_type="region", geo_slice="north-west", season="all", **base)
    assert nw.n_points == 3                                                      # Delhi, Rajasthan, Ladakh; no islands
    pooled = cell(C, geo_slice_type="pooled", geo_slice="all-points", season="all", **base)
    assert pooled.n_dates == 92 and pooled.status == "meets floor"
    hi = cell(C, geo_slice_type="high_altitude", geo_slice=">=1000m", season="all", **base)
    assert hi.n_points == 2 and hi.status == "insufficient sample" and "high-altitude" in hi.limitations
    st = cell(C, experiment="A2", comparison="single-model", model="gfs_global", variable="tmax", lead=1,
              geo_slice="VIDP", season="all", stratum="all")
    assert st.n_eligible == 92 and st.status == "meets floor"                   # station floor: >= 90 days


def test_d_rows_excluded_and_counted(tmp_path):
    src = FakeSource()
    src.add_month(MONTH, *build_month(MONTH, d_row=True))
    run_census.run(src, tmp_path / "o")
    C = pd.read_parquet(tmp_path / "o" / "census_cells.parquet")
    c = cell(C, experiment="A1", comparison="single-model", model="ecmwf_ifs025", variable="tmin", lead=3,
             geo_slice_type="pooled", geo_slice="all-points", season="all", stratum="all")
    assert c.excluded_D == 12 and c.n_eligible == 12 * (N_DAYS - 1)


def test_annotation_reclassifies_to_B_only_when_hashes_match(tmp_path):
    month = "2024-02"
    M, F, pairing = build_month(month, feb_archive_start=True)
    src = FakeSource()
    tag = src.add_month(month, M, F, pairing)
    sel = F[(F.model == "ecmwf_ifs025") & ~F.complete & F.reason.str.startswith("source hours missing")]
    keys = sorted(f"{x.point_id}|{x.variable}|{x.nominal_lead_day}|{x.valid_date_ist}|{x.hours_present}" for x in sel.itertuples())
    ann = {"id": "a1", "release": tag, "manifest_sha256": src.recs[month]["manifest_sha256"], "model": "ecmwf_ifs025",
           "variables": ["tmax"], "rows": len(sel), "row_keys_sha256": hashlib.sha256("\n".join(keys).encode()).hexdigest(),
           "reclassify": {"from": "C", "to": "B", "rows": len(sel)}}
    src.anns = [ann]
    rec = run_census.run(src, tmp_path / "o")
    C = pd.read_parquet(tmp_path / "o" / "census_cells.parquet")
    c = cell(C, experiment="A1", comparison="single-model", model="ecmwf_ifs025", variable="tmax", lead=1,
             geo_slice_type="pooled", geo_slice="all-points", season="all", stratum="all")
    assert c.excluded_B == 24 and c.excluded_C == 0 and rec["annotations_applied"][0]["rows"] == 24
    src.anns = [dict(ann, row_keys_sha256="0" * 64)]
    with pytest.raises(CensusError, match="row keys"):
        run_census.run(src, tmp_path / "o2")


def test_missing_is_never_zero(tmp_path):
    M, F, pairing = build_month(MONTH)
    i = M.index[(M.forecast_available) & (M.reference == "era5") & (M.variable == "tmax")][0]
    M.loc[i, "forecast_value"] = None                                            # available but no value
    src = FakeSource()
    src.add_month(MONTH, M, F, pairing)
    with pytest.raises(CensusError, match="never zero"):
        run_census.run(src, tmp_path / "o")


def test_rain_windows_never_mixed(tmp_path):
    M, F, pairing = build_month(MONTH)
    M.loc[(M.variable == "precip_0830") & (M.reference == "imd_rf025"), "window"] = "ist_day"
    src = FakeSource()
    src.add_month(MONTH, M, F, pairing)
    with pytest.raises(CensusError, match="never mixed"):
        run_census.run(src, tmp_path / "o")


def test_historical_prospective_separation(tmp_path):
    M, F, pairing = build_month(MONTH)
    src = FakeSource()
    src.add_month(MONTH, M, F, pairing, dataset="prospective_daily")
    with pytest.raises(CensusError, match="never mixed"):
        run_census.run(src, tmp_path / "o")
    M2 = M.copy()
    M2.loc[M2.index[0], "run_time_known"] = True
    src2 = FakeSource()
    src2.add_month(MONTH, M2, F, pairing)
    with pytest.raises(CensusError, match="historical nominal-lead"):
        run_census.run(src2, tmp_path / "o2")


def test_earth2studio_gfs_is_not_an_independent_model(tmp_path):
    M, F, pairing = build_month(MONTH)
    e2s = M[M.model == "gfs_global"].head(5).assign(model="e2s_gfs025").to_dict("records")
    src = FakeSource()
    src.add_month(MONTH, pd.concat([M, pd.DataFrame(e2s)]), F, pairing)
    with pytest.raises(CensusError, match="Earth2Studio"):
        run_census.run(src, tmp_path / "o")


def test_tampered_archive_is_refused(tmp_path):
    src = FakeSource()
    tag = src.add_month(MONTH, *build_month(MONTH))
    name = f"matched_history-{MONTH}.parquet"
    src.assets[tag][name] = src.assets[tag][name] + b"x"
    with pytest.raises(CensusError, match="tampered"):
        run_census.run(src, tmp_path / "o")
    src2 = FakeSource()
    src2.add_month(MONTH, *build_month(MONTH))
    src2.recs[MONTH]["manifest_sha256"] = "0" * 64                               # index disagrees with release
    with pytest.raises(CensusError, match="archive-index"):
        run_census.run(src2, tmp_path / "o2")
    src3 = FakeSource()
    t3 = src3.add_month(MONTH, *build_month(MONTH))
    src3.rel[t3] = {"draft": True, "immutable": False}
    with pytest.raises(CensusError, match="immutable"):
        run_census.run(src3, tmp_path / "o3")


def test_deterministic(tmp_path):
    src = FakeSource()
    src.add_month(MONTH, *build_month(MONTH))
    r1 = run_census.run(src, tmp_path / "a")
    r2 = run_census.run(src, tmp_path / "b")
    assert r1["result_sha256"] == r2["result_sha256"]
    assert (tmp_path / "a" / "census_cells.csv").read_bytes() == (tmp_path / "b" / "census_cells.csv").read_bytes()
