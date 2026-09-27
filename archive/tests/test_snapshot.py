"""Offline tests for archive/snapshot.py (no network): a synthetic store in CORE's NetCDF contract."""
import pathlib
import sys

import numpy as np
import pandas as pd
import pytest
import xarray as xr

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import snapshot  # noqa: E402


@pytest.fixture()
def store(tmp_path):
    # 00 UTC run, 3-hourly steps for 96 h. 00 UTC = 05:30 IST, so IST days start at 18:30 UTC.
    times = pd.date_range("2026-09-27T03:00", periods=32, freq="3h")
    lat = np.array([22.0, 22.25], dtype="float32")
    lon = np.array([72.0, 72.25], dtype="float32")
    shape = (len(times), 2, 2)
    hours = np.arange(len(times))[:, None, None] * 3 + np.zeros(shape)
    ds = xr.Dataset(
        {
            "tp": (("time", "lat", "lon"), np.ones(shape, dtype="float32")),  # 1 mm every 3 h
            "t2m": (("time", "lat", "lon"), (20 + hours / 10).astype("float32")),  # steadily warming
            "fg10m": (("time", "lat", "lon"), np.full(shape, 10.0, dtype="float32")),  # 10 m/s
        },
        coords={"time": times, "lat": lat, "lon": lon},
        attrs={"source": "NOAA GFS via Earth2Studio", "model": "GFS 0.25° (GFS_FX)", "issue_time": "2026-09-27T00:00:00+00:00"},
    )
    p = tmp_path / "gfs_2026092700.nc"
    ds.to_netcdf(p)
    return p


def test_daily_aggregation(store, tmp_path):
    out = snapshot.e2s_daily(store, tmp_path, "2026-09-27T06:00:00+00:00")
    assert out.name == "e2s_gfs_daily_2026092700.nc"
    ds = xr.open_dataset(out)
    # only complete IST days (8 three-hourly steps) are kept
    assert (ds.rain_mm.values == 8.0).all()
    assert list(ds.lead_day.values) == list(range(1, 1 + ds.sizes["ist_day"]))
    assert (ds.tmax_c > ds.tmin_c).all()
    assert np.allclose(ds.gust_max_kmh.values, 36.0)  # 10 m/s -> 36 km/h
    # provenance travels with the file
    for k in ("source", "model", "issue_time", "source_url", "retrieved_at", "method"):
        assert ds.attrs[k]


def test_points_file_is_fixed_and_valid():
    import json

    pts = json.loads((pathlib.Path(snapshot.__file__).parent / "points.json").read_text())["points"]
    assert len(pts) == 36
    assert len({p["id"] for p in pts}) == 36
    for p in pts:
        assert 5 <= p["lat"] <= 38 and 66 <= p["lon"] <= 99
