"""Analysis of source-probe run 36684062500 (reads probe_result.json only; no network). Reproduces every number in
probe_report.md. Section C is an offline simulation (inference), not source evidence."""
import collections, json, sys
import numpy as np
from scipy.interpolate import CubicSpline, PchipInterpolator

r = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "probe_result.json"))
A, B = r["questions"]["A"]["by_date"], r["questions"]["B"]["by_date"]
L = [str(n) for n in range(1, 8)]
print("archive check, max |probe-derived daily - archived daily| per question:")
for q, Q in (("A", A), ("B", B)):
    d = [L_[n]["archive_check"]["max_abs_diff"] for pp in Q.values() for L_ in pp.values() for n in L]
    k = sum(L_[n]["archive_check"]["n_compared"] for pp in Q.values() for L_ in pp.values() for n in L)
    print(f"  {q}: {max(d):.2e} over {k} daily values")
print("A. GFS wet 3-h groups with three equal values, by alignment offset; total; share by UTC hour mod 6")
for n in L:
    tot = {o: collections.Counter() for o in range(3)}
    s, T = np.zeros(6), 0.0
    for pp in A.values():
        for x in pp.values():
            for o in range(3):
                tot[o].update(x[n]["groups"][f"offset{o}"])
            v = np.array([y or 0 for y in x[n]["hourly_values"]])
            for h, y in enumerate(v):
                s[h % 6] += y
            T += v.sum()
    eq = " ".join(f"off{o}:{tot[o]['three_equal']}/{tot[o]['one_wet_hour'] + tot[o]['three_equal'] + tot[o]['varying']}"
                  for o in range(3))
    print(f"  L{n} {eq} total {T:.1f} mm share " + " ".join(f"{y / T:.2f}" for y in s))
print("B. ECMWF mean |2nd difference| by UTC hour mod 6; mean UTC-day range")
for n in L:
    sd, cnt, rng = np.zeros(6), np.zeros(6), []
    for pp in B.values():
        for x in pp.values():
            v = np.array(x[n]["hourly_values"], float)
            rng += [np.ptp(v[24 * k:24 * k + 24]) for k in range(3)]
            for i, y in enumerate(np.abs(v[:-2] - 2 * v[1:-1] + v[2:])):
                sd[(i + 1) % 6] += y
                cnt[(i + 1) % 6] += 1
    print(f"  L{n} " + " ".join(f"{y:.3f}" for y in sd / cnt) + f" range {np.mean(rng):.2f}")
print("C. (inference) lead-5 series thinned to 00/06/12/18 UTC nodes, re-interpolated: change in IST-day Tmax/Tmin")
R = []
for pp in B.values():
    for x in pp.values():
        v5, v6 = (np.array(x[k]["hourly_values"], float) for k in ("5", "6"))
        w, t = slice(19, 43), np.arange(72)
        nd = t[t % 6 == 0]
        lin, cs, pc = np.interp(t, nd, v5[nd]), CubicSpline(nd, v5[nd])(t), PchipInterpolator(nd, v5[nd])(t)
        R.append([v6[w].max() - v5[w].max(), lin[w].max() - v5[w].max(), cs[w].max() - v5[w].max(),
                  pc[w].max() - v5[w].max(), v6[w].min() - v5[w].min(), pc[w].min() - v5[w].min()])
R = np.array(R)
print("  Tmax observed L6-L5 %.2f | thinned linear %.2f spline %.2f pchip %.2f | Tmin observed %.2f thinned %.2f"
      % tuple(R.mean(0)))
