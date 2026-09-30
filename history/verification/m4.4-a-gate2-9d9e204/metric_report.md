# M4.4-A Gate 2 — bias, MAE, RMSE (VM-1.1, census m4.4-a-census-2@55030a4)

Months 2024-02 … 2026-08 (31 verified immutable releases); code 9d9e204; archive-index bb6714a. Error = forecast − reference. 95% intervals: percentile; 7-day non-overlapping calendar blocks of whole valid dates (all points together), 1000 resamples, master seed 20240201.

Cells computed: **9,585** (of 14,700 census cells); suppressed by the publication floor or not defined: **5,115** — no value was computed for them.

Differences are measured differences for the stated population, reference, metric and period only. They do not show that any model is better in general. No overall score and no model ranking are produced. † = the 95% interval excludes 0 (bias and differences only).

## Primary — temperature vs METAR (per station, all seasons, leads 1–6)

| Cell | Subject | n | Bias [95% CI] | MAE [95% CI] | RMSE [95% CI] |
| --- | --- | --- | --- | --- | --- |
| A2 · single-model · ecmwf_ifs025 · tmax · L1 · station=VEIM | ecmwf_ifs025 | 541 | -1.44 [-1.63, -1.26] † | +1.71 [+1.57, +1.86] | +2.08 [+1.93, +2.23] |
| A2 · single-model · ecmwf_ifs025 · tmax · L1 · station=VICG | ecmwf_ifs025 | 139 | -1.65 [-1.99, -1.33] † | +2.05 [+1.79, +2.32] | +2.39 [+2.10, +2.67] |
| A2 · single-model · ecmwf_ifs025 · tmax · L1 · station=VIDP | ecmwf_ifs025 | 936 | -0.69 [-0.85, -0.54] † | +1.36 [+1.27, +1.45] | +1.71 [+1.60, +1.82] |
| A2 · single-model · ecmwf_ifs025 · tmax · L1 · station=VOTR | ecmwf_ifs025 | 939 | -1.81 [-1.96, -1.65] † | +1.98 [+1.84, +2.11] | +2.31 [+2.17, +2.44] |
| A2 · single-model · ecmwf_ifs025 · tmax · L2 · station=VEIM | ecmwf_ifs025 | 541 | -1.33 [-1.52, -1.10] † | +1.72 [+1.57, +1.88] | +2.14 [+1.97, +2.31] |
| A2 · single-model · ecmwf_ifs025 · tmax · L2 · station=VICG | ecmwf_ifs025 | 138 | -1.51 [-1.91, -1.13] † | +2.00 [+1.73, +2.28] | +2.35 [+2.07, +2.64] |
| A2 · single-model · ecmwf_ifs025 · tmax · L2 · station=VIDP | ecmwf_ifs025 | 935 | -0.64 [-0.84, -0.45] † | +1.48 [+1.37, +1.59] | +1.85 [+1.73, +1.98] |
| A2 · single-model · ecmwf_ifs025 · tmax · L2 · station=VOTR | ecmwf_ifs025 | 938 | -1.75 [-1.93, -1.58] † | +1.98 [+1.84, +2.11] | +2.34 [+2.21, +2.47] |
| A2 · single-model · ecmwf_ifs025 · tmax · L3 · station=VEIM | ecmwf_ifs025 | 540 | -1.27 [-1.53, -1.03] † | +1.77 [+1.61, +1.95] | +2.25 [+2.06, +2.46] |
| A2 · single-model · ecmwf_ifs025 · tmax · L3 · station=VICG | ecmwf_ifs025 | 138 | -1.41 [-1.88, -0.96] † | +2.01 [+1.77, +2.29] | +2.32 [+2.06, +2.65] |
| A2 · single-model · ecmwf_ifs025 · tmax · L3 · station=VIDP | ecmwf_ifs025 | 934 | -0.49 [-0.71, -0.26] † | +1.55 [+1.42, +1.66] | +2.00 [+1.83, +2.15] |
| A2 · single-model · ecmwf_ifs025 · tmax · L3 · station=VOTR | ecmwf_ifs025 | 937 | -1.66 [-1.84, -1.48] † | +1.96 [+1.82, +2.09] | +2.36 [+2.23, +2.49] |
| A2 · single-model · ecmwf_ifs025 · tmax · L4 · station=VEIM | ecmwf_ifs025 | 540 | -1.18 [-1.45, -0.93] † | +1.73 [+1.56, +1.92] | +2.22 [+2.01, +2.44] |
| A2 · single-model · ecmwf_ifs025 · tmax · L4 · station=VICG | ecmwf_ifs025 | 137 | -1.20 [-1.71, -0.68] † | +1.99 [+1.74, +2.27] | +2.34 [+2.04, +2.66] |
| A2 · single-model · ecmwf_ifs025 · tmax · L4 · station=VIDP | ecmwf_ifs025 | 933 | -0.34 [-0.57, -0.06] † | +1.65 [+1.52, +1.79] | +2.13 [+1.95, +2.31] |
| A2 · single-model · ecmwf_ifs025 · tmax · L4 · station=VOTR | ecmwf_ifs025 | 936 | -1.64 [-1.82, -1.45] † | +1.95 [+1.82, +2.10] | +2.38 [+2.24, +2.52] |
| A2 · single-model · ecmwf_ifs025 · tmax · L5 · station=VEIM | ecmwf_ifs025 | 540 | -1.12 [-1.40, -0.86] † | +1.81 [+1.63, +2.01] | +2.31 [+2.10, +2.53] |
| A2 · single-model · ecmwf_ifs025 · tmax · L5 · station=VICG | ecmwf_ifs025 | 136 | -1.15 [-1.75, -0.49] † | +2.10 [+1.83, +2.37] | +2.50 [+2.21, +2.78] |
| A2 · single-model · ecmwf_ifs025 · tmax · L5 · station=VIDP | ecmwf_ifs025 | 932 | -0.28 [-0.54, -0.01] † | +1.75 [+1.60, +1.92] | +2.28 [+2.08, +2.50] |
| A2 · single-model · ecmwf_ifs025 · tmax · L5 · station=VOTR | ecmwf_ifs025 | 935 | -1.58 [-1.77, -1.39] † | +1.95 [+1.81, +2.09] | +2.35 [+2.22, +2.49] |
| A2 · single-model · ecmwf_ifs025 · tmax · L6 · station=VEIM | ecmwf_ifs025 | 539 | -1.56 [-1.82, -1.30] † | +2.03 [+1.85, +2.24] | +2.58 [+2.35, +2.81] |
| A2 · single-model · ecmwf_ifs025 · tmax · L6 · station=VICG | ecmwf_ifs025 | 135 | -1.27 [-2.06, -0.53] † | +2.36 [+2.04, +2.72] | +2.85 [+2.50, +3.21] |
| A2 · single-model · ecmwf_ifs025 · tmax · L6 · station=VIDP | ecmwf_ifs025 | 931 | -1.16 [-1.44, -0.84] † | +2.27 [+2.11, +2.44] | +2.76 [+2.58, +2.96] |
| A2 · single-model · ecmwf_ifs025 · tmax · L6 · station=VOTR | ecmwf_ifs025 | 934 | -2.44 [-2.61, -2.27] † | +2.61 [+2.45, +2.75] | +2.99 [+2.83, +3.14] |
| A2 · single-model · ecmwf_ifs025 · tmin · L1 · station=VEIM | ecmwf_ifs025 | 541 | -0.22 [-0.51, +0.06] | +1.54 [+1.44, +1.63] | +1.80 [+1.70, +1.91] |
| A2 · single-model · ecmwf_ifs025 · tmin · L1 · station=VICG | ecmwf_ifs025 | 139 | -0.52 [-0.94, -0.09] † | +1.59 [+1.25, +2.05] | +2.75 [+1.67, +4.06] |
| A2 · single-model · ecmwf_ifs025 · tmin · L1 · station=VIDP | ecmwf_ifs025 | 936 | -1.45 [-1.58, -1.31] † | +1.74 [+1.64, +1.84] | +2.08 [+1.97, +2.19] |
| A2 · single-model · ecmwf_ifs025 · tmin · L1 · station=VOTR | ecmwf_ifs025 | 939 | -1.36 [-1.47, -1.23] † | +1.53 [+1.44, +1.62] | +1.77 [+1.68, +1.85] |
| A2 · single-model · ecmwf_ifs025 · tmin · L2 · station=VEIM | ecmwf_ifs025 | 541 | -0.15 [-0.42, +0.17] | +1.53 [+1.42, +1.64] | +1.82 [+1.70, +1.94] |
| A2 · single-model · ecmwf_ifs025 · tmin · L2 · station=VICG | ecmwf_ifs025 | 138 | -0.51 [-0.86, -0.11] † | +1.61 [+1.28, +2.04] | +2.71 [+1.63, +3.95] |
| A2 · single-model · ecmwf_ifs025 · tmin · L2 · station=VIDP | ecmwf_ifs025 | 935 | -1.48 [-1.64, -1.33] † | +1.82 [+1.72, +1.92] | +2.19 [+2.07, +2.29] |
| A2 · single-model · ecmwf_ifs025 · tmin · L2 · station=VOTR | ecmwf_ifs025 | 938 | -1.42 [-1.54, -1.30] † | +1.59 [+1.50, +1.68] | +1.84 [+1.74, +1.93] |
| A2 · single-model · ecmwf_ifs025 · tmin · L3 · station=VEIM | ecmwf_ifs025 | 540 | -0.08 [-0.36, +0.20] | +1.49 [+1.38, +1.60] | +1.80 [+1.67, +1.91] |
| A2 · single-model · ecmwf_ifs025 · tmin · L3 · station=VICG | ecmwf_ifs025 | 138 | -0.58 [-1.01, -0.07] † | +1.58 [+1.28, +2.02] | +2.71 [+1.65, +4.03] |
| A2 · single-model · ecmwf_ifs025 · tmin · L3 · station=VIDP | ecmwf_ifs025 | 934 | -1.51 [-1.68, -1.32] † | +1.91 [+1.80, +2.02] | +2.28 [+2.17, +2.39] |
| A2 · single-model · ecmwf_ifs025 · tmin · L3 · station=VOTR | ecmwf_ifs025 | 937 | -1.45 [-1.56, -1.32] † | +1.63 [+1.55, +1.72] | +1.87 [+1.78, +1.96] |
| A2 · single-model · ecmwf_ifs025 · tmin · L4 · station=VEIM | ecmwf_ifs025 | 540 | -0.05 [-0.34, +0.24] | +1.52 [+1.41, +1.64] | +1.82 [+1.69, +1.95] |
| A2 · single-model · ecmwf_ifs025 · tmin · L4 · station=VICG | ecmwf_ifs025 | 137 | -0.32 [-0.75, +0.15] | +1.58 [+1.22, +2.06] | +2.73 [+1.60, +4.08] |
| A2 · single-model · ecmwf_ifs025 · tmin · L4 · station=VIDP | ecmwf_ifs025 | 933 | -1.46 [-1.63, -1.26] † | +1.93 [+1.83, +2.04] | +2.31 [+2.20, +2.43] |
| A2 · single-model · ecmwf_ifs025 · tmin · L4 · station=VOTR | ecmwf_ifs025 | 936 | -1.42 [-1.54, -1.31] † | +1.62 [+1.53, +1.70] | +1.86 [+1.78, +1.95] |
| A2 · single-model · ecmwf_ifs025 · tmin · L5 · station=VEIM | ecmwf_ifs025 | 540 | -0.05 [-0.33, +0.26] | +1.56 [+1.44, +1.69] | +1.89 [+1.74, +2.04] |
| A2 · single-model · ecmwf_ifs025 · tmin · L5 · station=VICG | ecmwf_ifs025 | 136 | -0.31 [-0.74, +0.23] | +1.51 [+1.15, +1.98] | +2.69 [+1.57, +3.98] |
| A2 · single-model · ecmwf_ifs025 · tmin · L5 · station=VIDP | ecmwf_ifs025 | 932 | -1.46 [-1.65, -1.24] † | +1.96 [+1.84, +2.09] | +2.37 [+2.23, +2.51] |
| A2 · single-model · ecmwf_ifs025 · tmin · L5 · station=VOTR | ecmwf_ifs025 | 935 | -1.46 [-1.58, -1.34] † | +1.66 [+1.58, +1.74] | +1.91 [+1.82, +1.99] |
| A2 · single-model · ecmwf_ifs025 · tmin · L6 · station=VEIM | ecmwf_ifs025 | 539 | -0.18 [-0.45, +0.10] | +1.53 [+1.42, +1.66] | +1.84 [+1.72, +1.98] |
| A2 · single-model · ecmwf_ifs025 · tmin · L6 · station=VICG | ecmwf_ifs025 | 135 | -0.34 [-0.76, +0.19] | +1.59 [+1.20, +2.08] | +2.79 [+1.60, +4.08] |
| A2 · single-model · ecmwf_ifs025 · tmin · L6 · station=VIDP | ecmwf_ifs025 | 931 | -1.68 [-1.90, -1.47] † | +2.15 [+2.02, +2.27] | +2.56 [+2.41, +2.70] |
| A2 · single-model · ecmwf_ifs025 · tmin · L6 · station=VOTR | ecmwf_ifs025 | 934 | -1.73 [-1.85, -1.61] † | +1.89 [+1.80, +1.97] | +2.13 [+2.05, +2.22] |
| A2 · single-model · gfs_global · tmax · L1 · station=VEIM | gfs_global | 541 | +0.36 [-0.11, +0.88] | +2.45 [+2.22, +2.67] | +2.98 [+2.70, +3.24] |
| A2 · single-model · gfs_global · tmax · L1 · station=VICG | gfs_global | 143 | +3.07 [+2.37, +3.78] † | +3.29 [+2.69, +3.91] | +3.92 [+3.22, +4.59] |
| A2 · single-model · gfs_global · tmax · L1 · station=VIDP | gfs_global | 940 | +3.20 [+2.97, +3.43] † | +3.25 [+3.01, +3.48] | +3.78 [+3.52, +4.02] |
| A2 · single-model · gfs_global · tmax · L1 · station=VOTR | gfs_global | 943 | -1.37 [-1.59, -1.16] † | +1.75 [+1.60, +1.92] | +2.25 [+2.05, +2.45] |
| A2 · single-model · gfs_global · tmax · L2 · station=VEIM | gfs_global | 541 | +0.43 [-0.08, +0.93] | +2.58 [+2.35, +2.80] | +3.14 [+2.88, +3.42] |
| A2 · single-model · gfs_global · tmax · L2 · station=VICG | gfs_global | 143 | +3.36 [+2.58, +4.08] † | +3.70 [+2.97, +4.41] | +4.43 [+3.61, +5.14] |
| A2 · single-model · gfs_global · tmax · L2 · station=VIDP | gfs_global | 940 | +3.48 [+3.24, +3.73] † | +3.54 [+3.30, +3.79] | +4.11 [+3.83, +4.38] |
| A2 · single-model · gfs_global · tmax · L2 · station=VOTR | gfs_global | 943 | -1.19 [-1.41, -0.97] † | +1.70 [+1.55, +1.86] | +2.21 [+2.03, +2.41] |
| A2 · single-model · gfs_global · tmax · L3 · station=VEIM | gfs_global | 541 | +0.50 [-0.02, +1.04] | +2.64 [+2.40, +2.88] | +3.21 [+2.93, +3.50] |
| A2 · single-model · gfs_global · tmax · L3 · station=VICG | gfs_global | 143 | +3.33 [+2.49, +4.15] † | +3.68 [+2.92, +4.40] | +4.43 [+3.66, +5.13] |
| A2 · single-model · gfs_global · tmax · L3 · station=VIDP | gfs_global | 940 | +3.54 [+3.26, +3.83] † | +3.63 [+3.36, +3.91] | +4.26 [+3.94, +4.59] |
| A2 · single-model · gfs_global · tmax · L3 · station=VOTR | gfs_global | 943 | -1.09 [-1.32, -0.87] † | +1.67 [+1.53, +1.82] | +2.21 [+1.99, +2.42] |
| A2 · single-model · gfs_global · tmax · L4 · station=VEIM | gfs_global | 541 | +0.46 [-0.02, +0.96] | +2.63 [+2.42, +2.84] | +3.21 [+2.99, +3.44] |
| A2 · single-model · gfs_global · tmax · L4 · station=VICG | gfs_global | 143 | +3.29 [+2.40, +4.20] † | +3.77 [+3.06, +4.49] | +4.55 [+3.80, +5.30] |
| A2 · single-model · gfs_global · tmax · L4 · station=VIDP | gfs_global | 940 | +3.53 [+3.24, +3.84] † | +3.68 [+3.41, +3.96] | +4.34 [+4.01, +4.67] |
| A2 · single-model · gfs_global · tmax · L4 · station=VOTR | gfs_global | 943 | -1.05 [-1.29, -0.81] † | +1.76 [+1.60, +1.92] | +2.35 [+2.13, +2.58] |
| A2 · single-model · gfs_global · tmax · L5 · station=VEIM | gfs_global | 541 | +0.48 [-0.04, +0.98] | +2.75 [+2.53, +2.96] | +3.35 [+3.10, +3.59] |
| A2 · single-model · gfs_global · tmax · L5 · station=VICG | gfs_global | 143 | +3.40 [+2.38, +4.37] † | +3.90 [+3.11, +4.67] | +4.78 [+4.00, +5.50] |
| A2 · single-model · gfs_global · tmax · L5 · station=VIDP | gfs_global | 940 | +3.51 [+3.22, +3.86] † | +3.69 [+3.43, +4.00] | +4.38 [+4.06, +4.72] |
| A2 · single-model · gfs_global · tmax · L5 · station=VOTR | gfs_global | 943 | -1.11 [-1.37, -0.87] † | +1.83 [+1.66, +1.99] | +2.41 [+2.18, +2.63] |
| A2 · single-model · gfs_global · tmax · L6 · station=VEIM | gfs_global | 541 | +0.48 [-0.03, +1.00] | +2.88 [+2.62, +3.13] | +3.52 [+3.24, +3.82] |
| A2 · single-model · gfs_global · tmax · L6 · station=VICG | gfs_global | 143 | +3.58 [+2.55, +4.56] † | +4.12 [+3.31, +4.92] | +5.03 [+4.22, +5.77] |
| A2 · single-model · gfs_global · tmax · L6 · station=VIDP | gfs_global | 940 | +3.58 [+3.28, +3.89] † | +3.79 [+3.51, +4.08] | +4.48 [+4.17, +4.80] |
| A2 · single-model · gfs_global · tmax · L6 · station=VOTR | gfs_global | 943 | -1.10 [-1.34, -0.86] † | +1.86 [+1.69, +2.04] | +2.47 [+2.23, +2.73] |
| A2 · single-model · gfs_global · tmin · L1 · station=VEIM | gfs_global | 541 | -1.80 [-1.96, -1.62] † | +1.94 [+1.80, +2.07] | +2.25 [+2.12, +2.38] |
| A2 · single-model · gfs_global · tmin · L1 · station=VICG | gfs_global | 143 | +1.86 [+1.14, +2.58] † | +2.40 [+1.92, +2.92] | +3.40 [+2.43, +4.56] |
| A2 · single-model · gfs_global · tmin · L1 · station=VIDP | gfs_global | 940 | +4.62 [+4.36, +4.90] † | +4.65 [+4.39, +4.92] | +5.11 [+4.87, +5.36] |
| A2 · single-model · gfs_global · tmin · L1 · station=VOTR | gfs_global | 943 | -1.29 [-1.46, -1.13] † | +1.61 [+1.51, +1.72] | +1.88 [+1.78, +1.98] |
| A2 · single-model · gfs_global · tmin · L2 · station=VEIM | gfs_global | 541 | -1.69 [-1.85, -1.51] † | +1.91 [+1.78, +2.03] | +2.22 [+2.09, +2.34] |
| A2 · single-model · gfs_global · tmin · L2 · station=VICG | gfs_global | 143 | +1.97 [+1.14, +2.64] † | +2.60 [+2.03, +3.10] | +3.69 [+2.68, +4.84] |
| A2 · single-model · gfs_global · tmin · L2 · station=VIDP | gfs_global | 940 | +4.76 [+4.47, +5.06] † | +4.79 [+4.51, +5.08] | +5.30 [+5.04, +5.57] |
| A2 · single-model · gfs_global · tmin · L2 · station=VOTR | gfs_global | 943 | -1.27 [-1.45, -1.12] † | +1.60 [+1.51, +1.71] | +1.90 [+1.79, +2.00] |
| A2 · single-model · gfs_global · tmin · L3 · station=VEIM | gfs_global | 541 | -1.60 [-1.79, -1.41] † | +1.88 [+1.75, +2.00] | +2.19 [+2.07, +2.31] |
| A2 · single-model · gfs_global · tmin · L3 · station=VICG | gfs_global | 143 | +2.03 [+1.27, +2.76] † | +2.76 [+2.24, +3.24] | +3.84 [+2.84, +4.94] |
| A2 · single-model · gfs_global · tmin · L3 · station=VIDP | gfs_global | 940 | +4.70 [+4.36, +5.04] † | +4.78 [+4.47, +5.11] | +5.34 [+5.04, +5.63] |
| A2 · single-model · gfs_global · tmin · L3 · station=VOTR | gfs_global | 943 | -1.27 [-1.44, -1.09] † | +1.64 [+1.53, +1.74] | +1.95 [+1.84, +2.05] |
| A2 · single-model · gfs_global · tmin · L4 · station=VEIM | gfs_global | 541 | -1.49 [-1.69, -1.29] † | +1.82 [+1.69, +1.95] | +2.15 [+2.02, +2.27] |
| A2 · single-model · gfs_global · tmin · L4 · station=VICG | gfs_global | 143 | +1.86 [+1.00, +2.67] † | +2.70 [+2.15, +3.20] | +3.83 [+2.81, +5.01] |
| A2 · single-model · gfs_global · tmin · L4 · station=VIDP | gfs_global | 940 | +4.67 [+4.31, +5.01] † | +4.76 [+4.44, +5.08] | +5.36 [+5.09, +5.65] |
| A2 · single-model · gfs_global · tmin · L4 · station=VOTR | gfs_global | 943 | -1.28 [-1.45, -1.10] † | +1.66 [+1.55, +1.78] | +1.98 [+1.87, +2.10] |
| A2 · single-model · gfs_global · tmin · L5 · station=VEIM | gfs_global | 541 | -1.55 [-1.74, -1.35] † | +1.86 [+1.73, +1.99] | +2.18 [+2.05, +2.30] |
| A2 · single-model · gfs_global · tmin · L5 · station=VICG | gfs_global | 143 | +1.95 [+1.14, +2.84] † | +2.73 [+2.20, +3.30] | +3.84 [+2.83, +5.06] |
| A2 · single-model · gfs_global · tmin · L5 · station=VIDP | gfs_global | 940 | +4.82 [+4.45, +5.19] † | +4.92 [+4.57, +5.28] | +5.55 [+5.25, +5.85] |
| A2 · single-model · gfs_global · tmin · L5 · station=VOTR | gfs_global | 943 | -1.30 [-1.48, -1.11] † | +1.68 [+1.56, +1.79] | +2.02 [+1.89, +2.13] |
| A2 · single-model · gfs_global · tmin · L6 · station=VEIM | gfs_global | 541 | -1.52 [-1.73, -1.32] † | +1.87 [+1.73, +2.01] | +2.19 [+2.06, +2.32] |
| A2 · single-model · gfs_global · tmin · L6 · station=VICG | gfs_global | 143 | +2.01 [+1.11, +2.90] † | +2.72 [+2.14, +3.27] | +3.91 [+2.81, +4.97] |
| A2 · single-model · gfs_global · tmin · L6 · station=VIDP | gfs_global | 940 | +4.84 [+4.43, +5.21] † | +4.96 [+4.59, +5.30] | +5.58 [+5.25, +5.86] |
| A2 · single-model · gfs_global · tmin · L6 · station=VOTR | gfs_global | 943 | -1.37 [-1.55, -1.19] † | +1.71 [+1.59, +1.82] | +2.06 [+1.93, +2.19] |
| A2 · single-model · icon_global · tmax · L1 · station=VEIM | icon_global | 538 | -2.22 [-2.56, -1.85] † | +2.57 [+2.27, +2.84] | +3.17 [+2.86, +3.44] |
| A2 · single-model · icon_global · tmax · L1 · station=VICG | icon_global | 143 | -0.14 [-0.52, +0.23] | +1.40 [+1.22, +1.59] | +1.77 [+1.55, +1.97] |
| A2 · single-model · icon_global · tmax · L1 · station=VIDP | icon_global | 936 | -0.42 [-0.58, -0.27] † | +1.28 [+1.18, +1.37] | +1.66 [+1.53, +1.77] |
| A2 · single-model · icon_global · tmax · L1 · station=VOTR | icon_global | 939 | -1.40 [-1.55, -1.26] † | +1.62 [+1.51, +1.74] | +2.01 [+1.88, +2.14] |
| A2 · single-model · icon_global · tmax · L2 · station=VEIM | icon_global | 541 | -2.12 [-2.51, -1.76] † | +2.57 [+2.29, +2.88] | +3.18 [+2.88, +3.48] |
| A2 · single-model · icon_global · tmax · L2 · station=VICG | icon_global | 143 | -0.24 [-0.62, +0.16] | +1.39 [+1.21, +1.57] | +1.81 [+1.57, +2.05] |
| A2 · single-model · icon_global · tmax · L2 · station=VIDP | icon_global | 940 | -0.47 [-0.65, -0.28] † | +1.47 [+1.36, +1.58] | +1.89 [+1.76, +2.02] |
| A2 · single-model · icon_global · tmax · L2 · station=VOTR | icon_global | 943 | -1.21 [-1.37, -1.06] † | +1.57 [+1.45, +1.68] | +1.95 [+1.82, +2.07] |
| A2 · single-model · icon_global · tmax · L3 · station=VEIM | icon_global | 538 | -2.01 [-2.38, -1.63] † | +2.48 [+2.19, +2.78] | +3.11 [+2.79, +3.40] |
| A2 · single-model · icon_global · tmax · L3 · station=VICG | icon_global | 143 | -0.17 [-0.64, +0.27] | +1.45 [+1.26, +1.67] | +1.90 [+1.66, +2.16] |
| A2 · single-model · icon_global · tmax · L3 · station=VIDP | icon_global | 936 | -0.38 [-0.58, -0.17] † | +1.55 [+1.43, +1.67] | +2.00 [+1.86, +2.15] |
| A2 · single-model · icon_global · tmax · L3 · station=VOTR | icon_global | 939 | -1.04 [-1.20, -0.86] † | +1.52 [+1.41, +1.63] | +1.89 [+1.76, +2.00] |
| A2 · single-model · icon_global · tmax · L4 · station=VEIM | icon_global | 538 | -2.04 [-2.42, -1.64] † | +2.55 [+2.25, +2.85] | +3.19 [+2.86, +3.47] |
| A2 · single-model · icon_global · tmax · L4 · station=VICG | icon_global | 143 | -0.17 [-0.70, +0.35] | +1.71 [+1.53, +1.90] | +2.16 [+1.96, +2.34] |
| A2 · single-model · icon_global · tmax · L4 · station=VIDP | icon_global | 936 | -0.35 [-0.56, -0.13] † | +1.67 [+1.54, +1.79] | +2.18 [+2.01, +2.34] |
| A2 · single-model · icon_global · tmax · L4 · station=VOTR | icon_global | 939 | -0.91 [-1.10, -0.72] † | +1.55 [+1.43, +1.67] | +1.95 [+1.81, +2.08] |
| A2 · single-model · icon_global · tmax · L5 · station=VEIM | icon_global | 538 | -1.96 [-2.34, -1.56] † | +2.59 [+2.31, +2.89] | +3.28 [+2.98, +3.58] |
| A2 · single-model · icon_global · tmax · L5 · station=VICG | icon_global | 143 | +0.06 [-0.48, +0.65] | +1.77 [+1.50, +2.02] | +2.28 [+2.01, +2.52] |
| A2 · single-model · icon_global · tmax · L5 · station=VIDP | icon_global | 936 | -0.29 [-0.53, -0.04] † | +1.81 [+1.67, +1.96] | +2.31 [+2.13, +2.49] |
| A2 · single-model · icon_global · tmax · L5 · station=VOTR | icon_global | 939 | -0.72 [-0.97, -0.50] † | +1.60 [+1.48, +1.71] | +2.02 [+1.87, +2.15] |
| A2 · single-model · icon_global · tmax · L6 · station=VEIM | icon_global | 538 | -1.78 [-2.16, -1.40] † | +2.54 [+2.27, +2.81] | +3.17 [+2.88, +3.45] |
| A2 · single-model · icon_global · tmax · L6 · station=VICG | icon_global | 143 | +0.18 [-0.54, +0.99] | +2.16 [+1.79, +2.54] | +2.81 [+2.40, +3.19] |
| A2 · single-model · icon_global · tmax · L6 · station=VIDP | icon_global | 936 | -0.18 [-0.47, +0.10] | +1.93 [+1.79, +2.08] | +2.47 [+2.28, +2.66] |
| A2 · single-model · icon_global · tmax · L6 · station=VOTR | icon_global | 939 | -0.65 [-0.85, -0.44] † | +1.61 [+1.50, +1.73] | +2.04 [+1.91, +2.16] |
| A2 · single-model · icon_global · tmin · L1 · station=VEIM | icon_global | 538 | -0.75 [-1.02, -0.49] † | +1.56 [+1.42, +1.69] | +1.91 [+1.75, +2.04] |
| A2 · single-model · icon_global · tmin · L1 · station=VICG | icon_global | 143 | +0.68 [+0.27, +1.16] † | +1.36 [+1.07, +1.73] | +2.67 [+1.39, +4.16] |
| A2 · single-model · icon_global · tmin · L1 · station=VIDP | icon_global | 936 | -0.43 [-0.56, -0.29] † | +1.18 [+1.09, +1.27] | +1.54 [+1.42, +1.65] |
| A2 · single-model · icon_global · tmin · L1 · station=VOTR | icon_global | 939 | -1.41 [-1.54, -1.29] † | +1.64 [+1.56, +1.72] | +1.87 [+1.77, +1.95] |
| A2 · single-model · icon_global · tmin · L2 · station=VEIM | icon_global | 541 | -0.74 [-0.99, -0.47] † | +1.59 [+1.46, +1.73] | +1.93 [+1.79, +2.09] |
| A2 · single-model · icon_global · tmin · L2 · station=VICG | icon_global | 143 | +0.57 [+0.17, +1.13] † | +1.50 [+1.17, +1.95] | +2.73 [+1.54, +4.24] |
| A2 · single-model · icon_global · tmin · L2 · station=VIDP | icon_global | 940 | -0.52 [-0.68, -0.37] † | +1.29 [+1.21, +1.39] | +1.65 [+1.54, +1.78] |
| A2 · single-model · icon_global · tmin · L2 · station=VOTR | icon_global | 943 | -1.40 [-1.54, -1.26] † | +1.67 [+1.58, +1.76] | +1.91 [+1.81, +2.00] |
| A2 · single-model · icon_global · tmin · L3 · station=VEIM | icon_global | 538 | -0.72 [-0.98, -0.45] † | +1.58 [+1.44, +1.71] | +1.92 [+1.78, +2.06] |
| A2 · single-model · icon_global · tmin · L3 · station=VICG | icon_global | 143 | +0.55 [+0.08, +1.07] † | +1.50 [+1.18, +1.89] | +2.71 [+1.50, +4.27] |
| A2 · single-model · icon_global · tmin · L3 · station=VIDP | icon_global | 936 | -0.54 [-0.71, -0.39] † | +1.38 [+1.28, +1.47] | +1.78 [+1.65, +1.91] |
| A2 · single-model · icon_global · tmin · L3 · station=VOTR | icon_global | 939 | -1.36 [-1.50, -1.22] † | +1.63 [+1.54, +1.72] | +1.90 [+1.80, +1.99] |
| A2 · single-model · icon_global · tmin · L4 · station=VEIM | icon_global | 538 | -0.82 [-1.10, -0.55] † | +1.65 [+1.50, +1.79] | +2.03 [+1.85, +2.20] |
| A2 · single-model · icon_global · tmin · L4 · station=VICG | icon_global | 143 | +0.63 [+0.20, +1.09] † | +1.40 [+1.07, +1.81] | +2.71 [+1.45, +4.15] |
| A2 · single-model · icon_global · tmin · L4 · station=VIDP | icon_global | 936 | -0.46 [-0.62, -0.29] † | +1.38 [+1.29, +1.49] | +1.77 [+1.65, +1.92] |
| A2 · single-model · icon_global · tmin · L4 · station=VOTR | icon_global | 939 | -1.34 [-1.48, -1.20] † | +1.61 [+1.52, +1.71] | +1.88 [+1.79, +1.99] |
| A2 · single-model · icon_global · tmin · L5 · station=VEIM | icon_global | 538 | -0.81 [-1.12, -0.50] † | +1.71 [+1.56, +1.88] | +2.13 [+1.93, +2.33] |
| A2 · single-model · icon_global · tmin · L5 · station=VICG | icon_global | 143 | +0.51 [-0.00, +1.03] | +1.47 [+1.11, +1.87] | +2.76 [+1.45, +4.18] |
| A2 · single-model · icon_global · tmin · L5 · station=VIDP | icon_global | 936 | -0.46 [-0.65, -0.27] † | +1.41 [+1.31, +1.52] | +1.81 [+1.67, +1.96] |
| A2 · single-model · icon_global · tmin · L5 · station=VOTR | icon_global | 939 | -1.37 [-1.51, -1.23] † | +1.63 [+1.54, +1.73] | +1.89 [+1.79, +2.00] |
| A2 · single-model · icon_global · tmin · L6 · station=VEIM | icon_global | 538 | -0.83 [-1.14, -0.54] † | +1.73 [+1.57, +1.90] | +2.16 [+1.97, +2.35] |
| A2 · single-model · icon_global · tmin · L6 · station=VICG | icon_global | 143 | +0.57 [-0.00, +1.14] | +1.59 [+1.24, +2.00] | +2.83 [+1.60, +4.24] |
| A2 · single-model · icon_global · tmin · L6 · station=VIDP | icon_global | 936 | -0.45 [-0.65, -0.24] † | +1.46 [+1.36, +1.58] | +1.92 [+1.77, +2.07] |
| A2 · single-model · icon_global · tmin · L6 · station=VOTR | icon_global | 939 | -1.36 [-1.50, -1.22] † | +1.63 [+1.54, +1.72] | +1.90 [+1.81, +2.00] |

Model pairs on shared data:

| Cell | Subject | n | Bias [95% CI] | MAE [95% CI] | RMSE [95% CI] |
| --- | --- | --- | --- | --- | --- |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L1 · station=VEIM | difference: ecmwf_ifs025 minus gfs_global | 541 | -1.80 [-2.24, -1.34] † | -0.74 [-0.98, -0.48] † | -0.91 [-1.20, -0.60] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L1 · station=VEIM | ecmwf_ifs025 | 541 | -1.44 [-1.62, -1.24] † | +1.71 [+1.56, +1.86] | +2.08 [+1.91, +2.22] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L1 · station=VEIM | gfs_global | 541 | +0.36 [-0.18, +0.86] | +2.45 [+2.22, +2.68] | +2.98 [+2.70, +3.24] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L1 · station=VICG | difference: ecmwf_ifs025 minus gfs_global | 139 | -4.77 [-5.45, -4.11] † | -1.28 [-2.00, -0.57] † | -1.56 [-2.31, -0.76] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L1 · station=VICG | ecmwf_ifs025 | 139 | -1.65 [-1.99, -1.36] † | +2.05 [+1.79, +2.32] | +2.39 [+2.12, +2.68] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L1 · station=VICG | gfs_global | 139 | +3.12 [+2.43, +3.85] † | +3.33 [+2.73, +4.00] | +3.95 [+3.27, +4.63] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L1 · station=VIDP | difference: ecmwf_ifs025 minus gfs_global | 936 | -3.89 [-4.10, -3.69] † | -1.89 [-2.10, -1.66] † | -2.06 [-2.28, -1.82] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L1 · station=VIDP | ecmwf_ifs025 | 936 | -0.69 [-0.85, -0.54] † | +1.36 [+1.27, +1.45] | +1.71 [+1.61, +1.83] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L1 · station=VIDP | gfs_global | 936 | +3.20 [+2.96, +3.44] † | +3.25 [+3.03, +3.47] | +3.78 [+3.52, +4.02] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L1 · station=VOTR | difference: ecmwf_ifs025 minus gfs_global | 939 | -0.44 [-0.68, -0.21] † | +0.23 [+0.05, +0.41] † | +0.06 [-0.15, +0.27] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L1 · station=VOTR | ecmwf_ifs025 | 939 | -1.81 [-1.96, -1.65] † | +1.98 [+1.85, +2.11] | +2.31 [+2.18, +2.43] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L1 · station=VOTR | gfs_global | 939 | -1.37 [-1.56, -1.16] † | +1.75 [+1.60, +1.91] | +2.25 [+2.07, +2.44] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L2 · station=VEIM | difference: ecmwf_ifs025 minus gfs_global | 541 | -1.76 [-2.20, -1.35] † | -0.86 [-1.12, -0.62] † | -1.00 [-1.29, -0.72] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L2 · station=VEIM | ecmwf_ifs025 | 541 | -1.33 [-1.54, -1.11] † | +1.72 [+1.55, +1.88] | +2.14 [+1.96, +2.32] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L2 · station=VEIM | gfs_global | 541 | +0.43 [-0.07, +0.98] | +2.58 [+2.36, +2.81] | +3.14 [+2.90, +3.40] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L2 · station=VICG | difference: ecmwf_ifs025 minus gfs_global | 138 | -4.89 [-5.46, -4.25] † | -1.74 [-2.57, -0.86] † | -2.11 [-2.98, -1.17] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L2 · station=VICG | ecmwf_ifs025 | 138 | -1.51 [-1.92, -1.15] † | +2.00 [+1.74, +2.29] | +2.35 [+2.07, +2.64] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L2 · station=VICG | gfs_global | 138 | +3.38 [+2.58, +4.14] † | +3.74 [+2.98, +4.44] | +4.46 [+3.65, +5.23] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L2 · station=VIDP | difference: ecmwf_ifs025 minus gfs_global | 935 | -4.12 [-4.34, -3.92] † | -2.06 [-2.30, -1.83] † | -2.26 [-2.49, -2.00] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L2 · station=VIDP | ecmwf_ifs025 | 935 | -0.64 [-0.85, -0.44] † | +1.48 [+1.38, +1.59] | +1.85 [+1.72, +1.99] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L2 · station=VIDP | gfs_global | 935 | +3.48 [+3.23, +3.74] † | +3.54 [+3.28, +3.79] | +4.11 [+3.81, +4.39] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L2 · station=VOTR | difference: ecmwf_ifs025 minus gfs_global | 938 | -0.56 [-0.78, -0.34] † | +0.28 [+0.13, +0.44] † | +0.12 [-0.05, +0.31] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L2 · station=VOTR | ecmwf_ifs025 | 938 | -1.75 [-1.92, -1.58] † | +1.98 [+1.84, +2.10] | +2.34 [+2.21, +2.47] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L2 · station=VOTR | gfs_global | 938 | -1.19 [-1.40, -0.98] † | +1.70 [+1.56, +1.84] | +2.22 [+2.03, +2.40] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L3 · station=VEIM | difference: ecmwf_ifs025 minus gfs_global | 540 | -1.77 [-2.20, -1.36] † | -0.87 [-1.14, -0.62] † | -0.97 [-1.28, -0.66] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L3 · station=VEIM | ecmwf_ifs025 | 540 | -1.27 [-1.51, -1.05] † | +1.77 [+1.59, +1.94] | +2.25 [+2.05, +2.44] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L3 · station=VEIM | gfs_global | 540 | +0.50 [-0.01, +0.97] | +2.64 [+2.41, +2.89] | +3.22 [+2.93, +3.52] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L3 · station=VICG | difference: ecmwf_ifs025 minus gfs_global | 138 | -4.75 [-5.38, -4.14] † | -1.68 [-2.57, -0.75] † | -2.12 [-2.96, -1.18] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L3 · station=VICG | ecmwf_ifs025 | 138 | -1.41 [-1.87, -0.96] † | +2.01 [+1.76, +2.25] | +2.32 [+2.03, +2.61] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L3 · station=VICG | gfs_global | 138 | +3.33 [+2.54, +4.17] † | +3.69 [+2.88, +4.47] | +4.45 [+3.65, +5.15] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L3 · station=VIDP | difference: ecmwf_ifs025 minus gfs_global | 934 | -4.02 [-4.25, -3.80] † | -2.08 [-2.32, -1.84] † | -2.26 [-2.51, -2.00] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L3 · station=VIDP | ecmwf_ifs025 | 934 | -0.49 [-0.71, -0.25] † | +1.55 [+1.42, +1.67] | +2.00 [+1.83, +2.15] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L3 · station=VIDP | gfs_global | 934 | +3.54 [+3.26, +3.81] † | +3.63 [+3.35, +3.90] | +4.26 [+3.93, +4.59] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L3 · station=VOTR | difference: ecmwf_ifs025 minus gfs_global | 937 | -0.57 [-0.80, -0.34] † | +0.28 [+0.11, +0.43] † | +0.15 [-0.06, +0.34] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L3 · station=VOTR | ecmwf_ifs025 | 937 | -1.66 [-1.84, -1.49] † | +1.96 [+1.82, +2.09] | +2.36 [+2.23, +2.49] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L3 · station=VOTR | gfs_global | 937 | -1.09 [-1.32, -0.87] † | +1.68 [+1.53, +1.83] | +2.21 [+2.01, +2.44] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L4 · station=VEIM | difference: ecmwf_ifs025 minus gfs_global | 540 | -1.64 [-2.03, -1.22] † | -0.90 [-1.15, -0.64] † | -0.99 [-1.28, -0.72] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L4 · station=VEIM | ecmwf_ifs025 | 540 | -1.18 [-1.41, -0.94] † | +1.73 [+1.56, +1.92] | +2.22 [+2.02, +2.43] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L4 · station=VEIM | gfs_global | 540 | +0.46 [-0.02, +0.97] | +2.63 [+2.40, +2.86] | +3.21 [+2.96, +3.48] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L4 · station=VICG | difference: ecmwf_ifs025 minus gfs_global | 137 | -4.54 [-5.26, -3.82] † | -1.83 [-2.60, -0.90] † | -2.26 [-2.97, -1.34] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L4 · station=VICG | ecmwf_ifs025 | 137 | -1.20 [-1.69, -0.75] † | +1.99 [+1.73, +2.26] | +2.34 [+2.06, +2.65] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L4 · station=VICG | gfs_global | 137 | +3.34 [+2.32, +4.18] † | +3.82 [+3.00, +4.51] | +4.59 [+3.73, +5.31] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L4 · station=VIDP | difference: ecmwf_ifs025 minus gfs_global | 933 | -3.86 [-4.12, -3.66] † | -2.03 [-2.27, -1.79] † | -2.21 [-2.46, -1.96] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L4 · station=VIDP | ecmwf_ifs025 | 933 | -0.34 [-0.58, -0.08] † | +1.65 [+1.51, +1.78] | +2.13 [+1.95, +2.31] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L4 · station=VIDP | gfs_global | 933 | +3.53 [+3.23, +3.86] † | +3.68 [+3.40, +3.98] | +4.34 [+3.99, +4.69] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L4 · station=VOTR | difference: ecmwf_ifs025 minus gfs_global | 936 | -0.58 [-0.82, -0.33] † | +0.19 [+0.02, +0.35] † | +0.01 [-0.20, +0.21] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L4 · station=VOTR | ecmwf_ifs025 | 936 | -1.64 [-1.80, -1.44] † | +1.95 [+1.82, +2.08] | +2.38 [+2.24, +2.52] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L4 · station=VOTR | gfs_global | 936 | -1.06 [-1.31, -0.81] † | +1.77 [+1.60, +1.94] | +2.36 [+2.14, +2.60] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L5 · station=VEIM | difference: ecmwf_ifs025 minus gfs_global | 540 | -1.60 [-1.98, -1.23] † | -0.95 [-1.21, -0.70] † | -1.04 [-1.34, -0.75] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L5 · station=VEIM | ecmwf_ifs025 | 540 | -1.12 [-1.40, -0.86] † | +1.81 [+1.63, +2.00] | +2.31 [+2.10, +2.53] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L5 · station=VEIM | gfs_global | 540 | +0.48 [-0.03, +0.99] | +2.76 [+2.55, +3.00] | +3.35 [+3.11, +3.61] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L5 · station=VICG | difference: ecmwf_ifs025 minus gfs_global | 136 | -4.58 [-5.31, -3.80] † | -1.85 [-2.76, -0.91] † | -2.31 [-3.08, -1.38] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L5 · station=VICG | ecmwf_ifs025 | 136 | -1.15 [-1.75, -0.56] † | +2.10 [+1.82, +2.39] | +2.50 [+2.22, +2.78] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L5 · station=VICG | gfs_global | 136 | +3.43 [+2.43, +4.40] † | +3.95 [+3.09, +4.78] | +4.81 [+3.94, +5.50] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L5 · station=VIDP | difference: ecmwf_ifs025 minus gfs_global | 932 | -3.79 [-4.03, -3.56] † | -1.94 [-2.19, -1.70] † | -2.10 [-2.36, -1.84] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L5 · station=VIDP | ecmwf_ifs025 | 932 | -0.28 [-0.52, -0.02] † | +1.75 [+1.60, +1.91] | +2.28 [+2.08, +2.51] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L5 · station=VIDP | gfs_global | 932 | +3.51 [+3.21, +3.83] † | +3.69 [+3.42, +3.99] | +4.38 [+4.06, +4.73] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L5 · station=VOTR | difference: ecmwf_ifs025 minus gfs_global | 935 | -0.46 [-0.71, -0.20] † | +0.12 [-0.05, +0.29] | -0.07 [-0.27, +0.14] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L5 · station=VOTR | ecmwf_ifs025 | 935 | -1.58 [-1.78, -1.38] † | +1.95 [+1.81, +2.10] | +2.35 [+2.22, +2.50] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L5 · station=VOTR | gfs_global | 935 | -1.12 [-1.36, -0.90] † | +1.84 [+1.68, +2.01] | +2.42 [+2.21, +2.64] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L6 · station=VEIM | difference: ecmwf_ifs025 minus gfs_global | 539 | -2.05 [-2.45, -1.62] † | -0.85 [-1.13, -0.58] † | -0.94 [-1.27, -0.65] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L6 · station=VEIM | ecmwf_ifs025 | 539 | -1.56 [-1.82, -1.33] † | +2.03 [+1.86, +2.24] | +2.58 [+2.37, +2.83] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L6 · station=VEIM | gfs_global | 539 | +0.49 [-0.06, +1.01] | +2.88 [+2.64, +3.12] | +3.52 [+3.25, +3.81] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L6 · station=VICG | difference: ecmwf_ifs025 minus gfs_global | 135 | -4.88 [-5.62, -4.18] † | -1.81 [-2.87, -0.75] † | -2.20 [-3.15, -1.15] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L6 · station=VICG | ecmwf_ifs025 | 135 | -1.27 [-2.04, -0.58] † | +2.36 [+2.03, +2.72] | +2.85 [+2.49, +3.24] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L6 · station=VICG | gfs_global | 135 | +3.61 [+2.51, +4.67] † | +4.17 [+3.32, +5.04] | +5.05 [+4.18, +5.82] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L6 · station=VIDP | difference: ecmwf_ifs025 minus gfs_global | 931 | -4.73 [-5.02, -4.43] † | -1.52 [-1.84, -1.18] † | -1.72 [-2.05, -1.35] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L6 · station=VIDP | ecmwf_ifs025 | 931 | -1.16 [-1.48, -0.85] † | +2.27 [+2.10, +2.43] | +2.76 [+2.57, +2.96] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L6 · station=VIDP | gfs_global | 931 | +3.57 [+3.27, +3.89] † | +3.78 [+3.51, +4.07] | +4.48 [+4.13, +4.81] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L6 · station=VOTR | difference: ecmwf_ifs025 minus gfs_global | 934 | -1.33 [-1.58, -1.09] † | +0.74 [+0.55, +0.92] † | +0.51 [+0.29, +0.73] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L6 · station=VOTR | ecmwf_ifs025 | 934 | -2.44 [-2.62, -2.28] † | +2.61 [+2.47, +2.76] | +2.99 [+2.86, +3.14] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmax · L6 · station=VOTR | gfs_global | 934 | -1.11 [-1.37, -0.86] † | +1.87 [+1.69, +2.06] | +2.48 [+2.25, +2.75] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L1 · station=VEIM | difference: ecmwf_ifs025 minus gfs_global | 541 | +1.57 [+1.39, +1.77] † | -0.40 [-0.57, -0.23] † | -0.45 [-0.61, -0.30] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L1 · station=VEIM | ecmwf_ifs025 | 541 | -0.22 [-0.50, +0.05] | +1.54 [+1.44, +1.64] | +1.80 [+1.69, +1.92] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L1 · station=VEIM | gfs_global | 541 | -1.80 [-1.95, -1.62] † | +1.94 [+1.81, +2.07] | +2.25 [+2.13, +2.38] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L1 · station=VICG | difference: ecmwf_ifs025 minus gfs_global | 139 | -2.47 [-3.14, -1.86] † | -0.82 [-1.17, -0.49] † | -0.68 [-1.07, -0.43] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L1 · station=VICG | ecmwf_ifs025 | 139 | -0.52 [-0.91, -0.09] † | +1.59 [+1.25, +2.02] | +2.75 [+1.65, +4.02] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L1 · station=VICG | gfs_global | 139 | +1.95 [+1.26, +2.58] † | +2.41 [+1.91, +2.94] | +3.43 [+2.40, +4.59] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L1 · station=VIDP | difference: ecmwf_ifs025 minus gfs_global | 936 | -6.08 [-6.36, -5.78] † | -2.92 [-3.19, -2.65] † | -3.04 [-3.30, -2.79] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L1 · station=VIDP | ecmwf_ifs025 | 936 | -1.45 [-1.58, -1.31] † | +1.74 [+1.64, +1.83] | +2.08 [+1.96, +2.18] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L1 · station=VIDP | gfs_global | 936 | +4.63 [+4.35, +4.89] † | +4.66 [+4.39, +4.91] | +5.12 [+4.87, +5.35] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L1 · station=VOTR | difference: ecmwf_ifs025 minus gfs_global | 939 | -0.07 [-0.22, +0.07] | -0.08 [-0.18, +0.04] | -0.11 [-0.21, +0.00] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L1 · station=VOTR | ecmwf_ifs025 | 939 | -1.36 [-1.48, -1.24] † | +1.53 [+1.45, +1.61] | +1.77 [+1.68, +1.85] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L1 · station=VOTR | gfs_global | 939 | -1.28 [-1.45, -1.12] † | +1.61 [+1.51, +1.70] | +1.88 [+1.78, +1.97] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L2 · station=VEIM | difference: ecmwf_ifs025 minus gfs_global | 541 | +1.54 [+1.36, +1.71] † | -0.37 [-0.54, -0.21] † | -0.40 [-0.57, -0.24] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L2 · station=VEIM | ecmwf_ifs025 | 541 | -0.15 [-0.43, +0.13] | +1.53 [+1.43, +1.64] | +1.82 [+1.70, +1.94] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L2 · station=VEIM | gfs_global | 541 | -1.69 [-1.86, -1.50] † | +1.91 [+1.77, +2.04] | +2.22 [+2.10, +2.34] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L2 · station=VICG | difference: ecmwf_ifs025 minus gfs_global | 138 | -2.58 [-3.23, -1.85] † | -1.00 [-1.48, -0.51] † | -1.02 [-1.62, -0.64] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L2 · station=VICG | ecmwf_ifs025 | 138 | -0.51 [-0.87, -0.09] † | +1.61 [+1.28, +2.04] | +2.71 [+1.63, +3.95] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L2 · station=VICG | gfs_global | 138 | +2.08 [+1.30, +2.73] † | +2.62 [+2.09, +3.14] | +3.74 [+2.76, +4.90] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L2 · station=VIDP | difference: ecmwf_ifs025 minus gfs_global | 935 | -6.25 [-6.60, -5.94] † | -2.99 [-3.29, -2.72] † | -3.13 [-3.41, -2.88] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L2 · station=VIDP | ecmwf_ifs025 | 935 | -1.48 [-1.63, -1.33] † | +1.82 [+1.72, +1.92] | +2.19 [+2.07, +2.30] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L2 · station=VIDP | gfs_global | 935 | +4.77 [+4.49, +5.08] † | +4.81 [+4.54, +5.11] | +5.31 [+5.07, +5.58] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L2 · station=VOTR | difference: ecmwf_ifs025 minus gfs_global | 938 | -0.15 [-0.31, -0.01] † | -0.01 [-0.11, +0.12] | -0.06 [-0.16, +0.06] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L2 · station=VOTR | ecmwf_ifs025 | 938 | -1.42 [-1.55, -1.30] † | +1.59 [+1.51, +1.68] | +1.84 [+1.75, +1.93] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L2 · station=VOTR | gfs_global | 938 | -1.27 [-1.43, -1.09] † | +1.60 [+1.50, +1.70] | +1.89 [+1.79, +1.99] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L3 · station=VEIM | difference: ecmwf_ifs025 minus gfs_global | 540 | +1.53 [+1.36, +1.70] † | -0.39 [-0.55, -0.22] † | -0.40 [-0.56, -0.22] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L3 · station=VEIM | ecmwf_ifs025 | 540 | -0.08 [-0.33, +0.20] | +1.49 [+1.39, +1.60] | +1.80 [+1.67, +1.92] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L3 · station=VEIM | gfs_global | 540 | -1.60 [-1.78, -1.42] † | +1.88 [+1.76, +2.00] | +2.19 [+2.07, +2.32] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L3 · station=VICG | difference: ecmwf_ifs025 minus gfs_global | 138 | -2.71 [-3.42, -1.96] † | -1.20 [-1.65, -0.75] † | -1.17 [-1.74, -0.77] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L3 · station=VICG | ecmwf_ifs025 | 138 | -0.58 [-0.97, -0.08] † | +1.58 [+1.29, +2.01] | +2.71 [+1.67, +4.04] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L3 · station=VICG | gfs_global | 138 | +2.13 [+1.35, +2.87] † | +2.78 [+2.25, +3.29] | +3.88 [+2.89, +5.02] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L3 · station=VIDP | difference: ecmwf_ifs025 minus gfs_global | 934 | -6.21 [-6.55, -5.84] † | -2.88 [-3.19, -2.53] † | -3.06 [-3.36, -2.72] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L3 · station=VIDP | ecmwf_ifs025 | 934 | -1.51 [-1.67, -1.33] † | +1.91 [+1.80, +2.01] | +2.28 [+2.16, +2.39] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L3 · station=VIDP | gfs_global | 934 | +4.71 [+4.35, +5.03] † | +4.79 [+4.45, +5.10] | +5.35 [+5.03, +5.62] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L3 · station=VOTR | difference: ecmwf_ifs025 minus gfs_global | 937 | -0.18 [-0.34, -0.02] † | -0.01 [-0.11, +0.11] | -0.07 [-0.18, +0.04] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L3 · station=VOTR | ecmwf_ifs025 | 937 | -1.45 [-1.57, -1.33] † | +1.63 [+1.55, +1.72] | +1.87 [+1.79, +1.96] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L3 · station=VOTR | gfs_global | 937 | -1.27 [-1.44, -1.09] † | +1.64 [+1.53, +1.75] | +1.95 [+1.84, +2.06] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L4 · station=VEIM | difference: ecmwf_ifs025 minus gfs_global | 540 | +1.44 [+1.28, +1.60] † | -0.30 [-0.45, -0.12] † | -0.33 [-0.49, -0.14] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L4 · station=VEIM | ecmwf_ifs025 | 540 | -0.05 [-0.31, +0.22] | +1.52 [+1.41, +1.64] | +1.82 [+1.69, +1.96] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L4 · station=VEIM | gfs_global | 540 | -1.49 [-1.69, -1.30] † | +1.82 [+1.70, +1.94] | +2.15 [+2.03, +2.28] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L4 · station=VICG | difference: ecmwf_ifs025 minus gfs_global | 137 | -2.27 [-3.03, -1.54] † | -1.17 [-1.62, -0.74] † | -1.17 [-1.74, -0.79] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L4 · station=VICG | ecmwf_ifs025 | 137 | -0.32 [-0.75, +0.12] | +1.58 [+1.22, +2.04] | +2.73 [+1.63, +4.08] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L4 · station=VICG | gfs_global | 137 | +1.95 [+1.13, +2.81] † | +2.75 [+2.19, +3.29] | +3.90 [+2.84, +5.20] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L4 · station=VIDP | difference: ecmwf_ifs025 minus gfs_global | 933 | -6.13 [-6.51, -5.73] † | -2.83 [-3.15, -2.51] † | -3.05 [-3.34, -2.75] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L4 · station=VIDP | ecmwf_ifs025 | 933 | -1.46 [-1.64, -1.26] † | +1.93 [+1.82, +2.04] | +2.31 [+2.19, +2.41] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L4 · station=VIDP | gfs_global | 933 | +4.67 [+4.30, +5.03] † | +4.76 [+4.43, +5.10] | +5.36 [+5.07, +5.64] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L4 · station=VOTR | difference: ecmwf_ifs025 minus gfs_global | 936 | -0.15 [-0.31, +0.01] | -0.05 [-0.16, +0.07] | -0.12 [-0.23, -0.00] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L4 · station=VOTR | ecmwf_ifs025 | 936 | -1.42 [-1.53, -1.30] † | +1.62 [+1.53, +1.70] | +1.86 [+1.77, +1.94] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L4 · station=VOTR | gfs_global | 936 | -1.28 [-1.45, -1.09] † | +1.66 [+1.55, +1.77] | +1.98 [+1.87, +2.10] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L5 · station=VEIM | difference: ecmwf_ifs025 minus gfs_global | 540 | +1.50 [+1.32, +1.73] † | -0.30 [-0.48, -0.13] † | -0.29 [-0.49, -0.09] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L5 · station=VEIM | ecmwf_ifs025 | 540 | -0.05 [-0.32, +0.28] | +1.56 [+1.43, +1.69] | +1.89 [+1.73, +2.04] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L5 · station=VEIM | gfs_global | 540 | -1.55 [-1.75, -1.35] † | +1.86 [+1.74, +2.00] | +2.18 [+2.06, +2.31] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L5 · station=VICG | difference: ecmwf_ifs025 minus gfs_global | 136 | -2.36 [-3.12, -1.65] † | -1.29 [-1.72, -0.89] † | -1.23 [-1.82, -0.90] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L5 · station=VICG | ecmwf_ifs025 | 136 | -0.31 [-0.74, +0.22] | +1.51 [+1.13, +1.98] | +2.69 [+1.54, +4.02] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L5 · station=VICG | gfs_global | 136 | +2.06 [+1.17, +2.95] † | +2.80 [+2.26, +3.36] | +3.92 [+2.89, +5.16] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L5 · station=VIDP | difference: ecmwf_ifs025 minus gfs_global | 932 | -6.29 [-6.69, -5.87] † | -2.97 [-3.35, -2.59] † | -3.19 [-3.52, -2.87] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L5 · station=VIDP | ecmwf_ifs025 | 932 | -1.46 [-1.66, -1.24] † | +1.96 [+1.85, +2.08] | +2.37 [+2.23, +2.51] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L5 · station=VIDP | gfs_global | 932 | +4.83 [+4.43, +5.22] † | +4.93 [+4.56, +5.30] | +5.56 [+5.25, +5.87] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L5 · station=VOTR | difference: ecmwf_ifs025 minus gfs_global | 935 | -0.16 [-0.32, -0.00] † | -0.02 [-0.14, +0.09] | -0.11 [-0.23, +0.00] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L5 · station=VOTR | ecmwf_ifs025 | 935 | -1.46 [-1.58, -1.35] † | +1.66 [+1.58, +1.75] | +1.91 [+1.82, +1.99] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L5 · station=VOTR | gfs_global | 935 | -1.30 [-1.47, -1.13] † | +1.68 [+1.57, +1.80] | +2.02 [+1.91, +2.15] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L6 · station=VEIM | difference: ecmwf_ifs025 minus gfs_global | 539 | +1.34 [+1.16, +1.52] † | -0.33 [-0.50, -0.17] † | -0.34 [-0.51, -0.18] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L6 · station=VEIM | ecmwf_ifs025 | 539 | -0.18 [-0.47, +0.11] | +1.53 [+1.42, +1.65] | +1.84 [+1.71, +1.97] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L6 · station=VEIM | gfs_global | 539 | -1.52 [-1.72, -1.32] † | +1.87 [+1.74, +2.00] | +2.19 [+2.07, +2.32] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L6 · station=VICG | difference: ecmwf_ifs025 minus gfs_global | 135 | -2.43 [-3.21, -1.66] † | -1.20 [-1.70, -0.70] † | -1.20 [-1.71, -0.87] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L6 · station=VICG | ecmwf_ifs025 | 135 | -0.34 [-0.80, +0.21] | +1.59 [+1.20, +2.10] | +2.79 [+1.60, +4.21] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L6 · station=VICG | gfs_global | 135 | +2.09 [+1.16, +3.02] † | +2.79 [+2.17, +3.40] | +3.99 [+2.87, +5.39] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L6 · station=VIDP | difference: ecmwf_ifs025 minus gfs_global | 931 | -6.53 [-6.96, -6.08] † | -2.83 [-3.17, -2.45] † | -3.03 [-3.34, -2.68] † |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L6 · station=VIDP | ecmwf_ifs025 | 931 | -1.68 [-1.91, -1.46] † | +2.15 [+2.02, +2.27] | +2.56 [+2.41, +2.70] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L6 · station=VIDP | gfs_global | 931 | +4.85 [+4.45, +5.22] † | +4.97 [+4.60, +5.30] | +5.59 [+5.26, +5.89] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L6 · station=VOTR | difference: ecmwf_ifs025 minus gfs_global | 934 | -0.36 [-0.54, -0.20] † | +0.18 [+0.05, +0.30] † | +0.07 [-0.06, +0.19] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L6 · station=VOTR | ecmwf_ifs025 | 934 | -1.73 [-1.85, -1.61] † | +1.89 [+1.81, +1.98] | +2.13 [+2.05, +2.22] |
| A2 · shared-data:ecmwf_ifs025+gfs_global · - · tmin · L6 · station=VOTR | gfs_global | 934 | -1.37 [-1.55, -1.19] † | +1.71 [+1.60, +1.83] | +2.06 [+1.94, +2.18] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L1 · station=VEIM | difference: ecmwf_ifs025 minus icon_global | 538 | +0.78 [+0.48, +1.06] † | -0.86 [-1.09, -0.61] † | -1.10 [-1.32, -0.83] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L1 · station=VEIM | ecmwf_ifs025 | 538 | -1.44 [-1.63, -1.23] † | +1.71 [+1.55, +1.86] | +2.08 [+1.91, +2.23] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L1 · station=VEIM | icon_global | 538 | -2.22 [-2.57, -1.84] † | +2.57 [+2.28, +2.86] | +3.17 [+2.86, +3.46] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L1 · station=VICG | difference: ecmwf_ifs025 minus icon_global | 139 | -1.56 [-1.87, -1.25] † | +0.67 [+0.35, +0.99] † | +0.66 [+0.34, +0.99] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L1 · station=VICG | ecmwf_ifs025 | 139 | -1.65 [-1.99, -1.33] † | +2.05 [+1.80, +2.33] | +2.39 [+2.12, +2.68] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L1 · station=VICG | icon_global | 139 | -0.09 [-0.46, +0.29] | +1.37 [+1.21, +1.56] | +1.73 [+1.55, +1.94] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L1 · station=VIDP | difference: ecmwf_ifs025 minus icon_global | 932 | -0.27 [-0.43, -0.11] † | +0.08 [-0.01, +0.19] | +0.06 [-0.04, +0.16] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L1 · station=VIDP | ecmwf_ifs025 | 932 | -0.69 [-0.85, -0.53] † | +1.36 [+1.27, +1.45] | +1.71 [+1.61, +1.82] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L1 · station=VIDP | icon_global | 932 | -0.42 [-0.58, -0.25] † | +1.27 [+1.18, +1.37] | +1.65 [+1.54, +1.77] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L1 · station=VOTR | difference: ecmwf_ifs025 minus icon_global | 935 | -0.40 [-0.54, -0.26] † | +0.35 [+0.24, +0.47] † | +0.30 [+0.19, +0.42] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L1 · station=VOTR | ecmwf_ifs025 | 935 | -1.81 [-1.96, -1.63] † | +1.98 [+1.85, +2.11] | +2.31 [+2.18, +2.43] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L1 · station=VOTR | icon_global | 935 | -1.41 [-1.55, -1.26] † | +1.63 [+1.51, +1.74] | +2.01 [+1.88, +2.13] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L2 · station=VEIM | difference: ecmwf_ifs025 minus icon_global | 541 | +0.80 [+0.53, +1.06] † | -0.85 [-1.08, -0.64] † | -1.03 [-1.26, -0.80] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L2 · station=VEIM | ecmwf_ifs025 | 541 | -1.33 [-1.55, -1.10] † | +1.72 [+1.57, +1.89] | +2.14 [+1.97, +2.32] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L2 · station=VEIM | icon_global | 541 | -2.12 [-2.50, -1.77] † | +2.57 [+2.29, +2.87] | +3.18 [+2.87, +3.47] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L2 · station=VICG | difference: ecmwf_ifs025 minus icon_global | 138 | -1.31 [-1.63, -1.04] † | +0.61 [+0.28, +0.92] † | +0.55 [+0.21, +0.88] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L2 · station=VICG | ecmwf_ifs025 | 138 | -1.51 [-1.90, -1.12] † | +2.00 [+1.72, +2.29] | +2.35 [+2.07, +2.65] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L2 · station=VICG | icon_global | 138 | -0.20 [-0.58, +0.18] | +1.39 [+1.20, +1.58] | +1.80 [+1.55, +2.07] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L2 · station=VIDP | difference: ecmwf_ifs025 minus icon_global | 935 | -0.17 [-0.36, +0.01] | +0.01 [-0.09, +0.13] | -0.03 [-0.16, +0.08] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L2 · station=VIDP | ecmwf_ifs025 | 935 | -0.64 [-0.84, -0.44] † | +1.48 [+1.37, +1.58] | +1.85 [+1.72, +1.98] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L2 · station=VIDP | icon_global | 935 | -0.47 [-0.66, -0.30] † | +1.47 [+1.35, +1.58] | +1.89 [+1.76, +2.02] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L2 · station=VOTR | difference: ecmwf_ifs025 minus icon_global | 938 | -0.53 [-0.66, -0.41] † | +0.41 [+0.31, +0.52] † | +0.39 [+0.30, +0.50] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L2 · station=VOTR | ecmwf_ifs025 | 938 | -1.75 [-1.91, -1.58] † | +1.98 [+1.84, +2.10] | +2.34 [+2.21, +2.48] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L2 · station=VOTR | icon_global | 938 | -1.22 [-1.37, -1.07] † | +1.57 [+1.45, +1.69] | +1.95 [+1.83, +2.08] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L3 · station=VEIM | difference: ecmwf_ifs025 minus icon_global | 537 | +0.74 [+0.47, +1.01] † | -0.71 [-0.94, -0.48] † | -0.86 [-1.08, -0.63] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L3 · station=VEIM | ecmwf_ifs025 | 537 | -1.27 [-1.52, -1.04] † | +1.77 [+1.60, +1.94] | +2.25 [+2.05, +2.44] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L3 · station=VEIM | icon_global | 537 | -2.01 [-2.38, -1.63] † | +2.49 [+2.20, +2.77] | +3.11 [+2.81, +3.38] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L3 · station=VICG | difference: ecmwf_ifs025 minus icon_global | 138 | -1.29 [-1.60, -1.04] † | +0.56 [+0.29, +0.83] † | +0.43 [+0.14, +0.75] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L3 · station=VICG | ecmwf_ifs025 | 138 | -1.41 [-1.88, -0.98] † | +2.01 [+1.78, +2.28] | +2.32 [+2.07, +2.63] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L3 · station=VICG | icon_global | 138 | -0.12 [-0.60, +0.34] | +1.45 [+1.24, +1.68] | +1.89 [+1.64, +2.15] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L3 · station=VIDP | difference: ecmwf_ifs025 minus icon_global | 930 | -0.10 [-0.29, +0.08] | +0.00 [-0.10, +0.11] | +0.00 [-0.11, +0.11] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L3 · station=VIDP | ecmwf_ifs025 | 930 | -0.48 [-0.71, -0.25] † | +1.54 [+1.42, +1.66] | +2.00 [+1.84, +2.14] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L3 · station=VIDP | icon_global | 930 | -0.38 [-0.58, -0.18] † | +1.54 [+1.42, +1.65] | +1.99 [+1.85, +2.13] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L3 · station=VOTR | difference: ecmwf_ifs025 minus icon_global | 933 | -0.61 [-0.74, -0.48] † | +0.43 [+0.33, +0.54] † | +0.47 [+0.35, +0.58] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L3 · station=VOTR | ecmwf_ifs025 | 933 | -1.66 [-1.82, -1.48] † | +1.96 [+1.82, +2.09] | +2.36 [+2.22, +2.50] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L3 · station=VOTR | icon_global | 933 | -1.05 [-1.20, -0.88] † | +1.52 [+1.41, +1.63] | +1.89 [+1.77, +2.00] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L4 · station=VEIM | difference: ecmwf_ifs025 minus icon_global | 537 | +0.87 [+0.58, +1.15] † | -0.82 [-1.05, -0.57] † | -0.97 [-1.21, -0.69] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L4 · station=VEIM | ecmwf_ifs025 | 537 | -1.17 [-1.43, -0.92] † | +1.73 [+1.56, +1.91] | +2.22 [+2.02, +2.43] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L4 · station=VEIM | icon_global | 537 | -2.04 [-2.43, -1.67] † | +2.55 [+2.25, +2.85] | +3.19 [+2.87, +3.49] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L4 · station=VICG | difference: ecmwf_ifs025 minus icon_global | 137 | -1.11 [-1.46, -0.78] † | +0.30 [-0.02, +0.59] | +0.20 [-0.11, +0.49] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L4 · station=VICG | ecmwf_ifs025 | 137 | -1.20 [-1.70, -0.64] † | +1.99 [+1.73, +2.25] | +2.34 [+2.04, +2.65] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L4 · station=VICG | icon_global | 137 | -0.09 [-0.63, +0.42] | +1.69 [+1.52, +1.88] | +2.13 [+1.93, +2.33] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L4 · station=VIDP | difference: ecmwf_ifs025 minus icon_global | 929 | +0.02 [-0.17, +0.22] | -0.01 [-0.12, +0.09] | -0.04 [-0.15, +0.08] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L4 · station=VIDP | ecmwf_ifs025 | 929 | -0.33 [-0.58, -0.07] † | +1.65 [+1.52, +1.80] | +2.13 [+1.96, +2.33] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L4 · station=VIDP | icon_global | 929 | -0.35 [-0.57, -0.12] † | +1.67 [+1.55, +1.80] | +2.17 [+2.03, +2.34] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L4 · station=VOTR | difference: ecmwf_ifs025 minus icon_global | 932 | -0.71 [-0.87, -0.57] † | +0.41 [+0.31, +0.51] † | +0.42 [+0.32, +0.53] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L4 · station=VOTR | ecmwf_ifs025 | 932 | -1.63 [-1.83, -1.43] † | +1.95 [+1.82, +2.10] | +2.38 [+2.23, +2.53] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L4 · station=VOTR | icon_global | 932 | -0.92 [-1.11, -0.74] † | +1.55 [+1.43, +1.67] | +1.95 [+1.81, +2.09] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L5 · station=VEIM | difference: ecmwf_ifs025 minus icon_global | 537 | +0.84 [+0.57, +1.12] † | -0.78 [-0.99, -0.56] † | -0.97 [-1.20, -0.72] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L5 · station=VEIM | ecmwf_ifs025 | 537 | -1.12 [-1.39, -0.86] † | +1.81 [+1.63, +1.99] | +2.31 [+2.09, +2.53] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L5 · station=VEIM | icon_global | 537 | -1.97 [-2.34, -1.56] † | +2.59 [+2.30, +2.88] | +3.28 [+2.98, +3.57] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L5 · station=VICG | difference: ecmwf_ifs025 minus icon_global | 136 | -1.32 [-1.77, -0.90] † | +0.35 [-0.04, +0.76] | +0.24 [-0.13, +0.65] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L5 · station=VICG | ecmwf_ifs025 | 136 | -1.15 [-1.79, -0.56] † | +2.10 [+1.83, +2.39] | +2.50 [+2.21, +2.79] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L5 · station=VICG | icon_global | 136 | +0.17 [-0.39, +0.75] | +1.75 [+1.48, +2.01] | +2.26 [+1.98, +2.52] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L5 · station=VIDP | difference: ecmwf_ifs025 minus icon_global | 928 | +0.02 [-0.19, +0.23] | -0.06 [-0.18, +0.06] | -0.03 [-0.17, +0.12] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L5 · station=VIDP | ecmwf_ifs025 | 928 | -0.27 [-0.54, +0.00] | +1.75 [+1.61, +1.91] | +2.28 [+2.08, +2.50] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L5 · station=VIDP | icon_global | 928 | -0.29 [-0.56, -0.03] † | +1.81 [+1.67, +1.96] | +2.31 [+2.14, +2.49] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L5 · station=VOTR | difference: ecmwf_ifs025 minus icon_global | 931 | -0.84 [-1.00, -0.67] † | +0.36 [+0.25, +0.45] † | +0.34 [+0.23, +0.43] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L5 · station=VOTR | ecmwf_ifs025 | 931 | -1.58 [-1.76, -1.39] † | +1.95 [+1.82, +2.09] | +2.36 [+2.22, +2.49] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L5 · station=VOTR | icon_global | 931 | -0.74 [-0.95, -0.52] † | +1.60 [+1.48, +1.71] | +2.02 [+1.88, +2.16] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L6 · station=VEIM | difference: ecmwf_ifs025 minus icon_global | 536 | +0.21 [-0.06, +0.50] | -0.50 [-0.68, -0.32] † | -0.59 [-0.79, -0.37] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L6 · station=VEIM | ecmwf_ifs025 | 536 | -1.56 [-1.80, -1.31] † | +2.04 [+1.84, +2.24] | +2.58 [+2.35, +2.81] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L6 · station=VEIM | icon_global | 536 | -1.78 [-2.15, -1.35] † | +2.54 [+2.26, +2.80] | +3.17 [+2.87, +3.45] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L6 · station=VICG | difference: ecmwf_ifs025 minus icon_global | 135 | -1.54 [-2.05, -0.99] † | +0.25 [-0.31, +0.88] | +0.08 [-0.50, +0.74] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L6 · station=VICG | ecmwf_ifs025 | 135 | -1.27 [-2.02, -0.58] † | +2.36 [+2.02, +2.73] | +2.85 [+2.50, +3.24] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L6 · station=VICG | icon_global | 135 | +0.27 [-0.44, +1.02] | +2.11 [+1.72, +2.50] | +2.77 [+2.31, +3.17] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L6 · station=VIDP | difference: ecmwf_ifs025 minus icon_global | 927 | -0.97 [-1.23, -0.73] † | +0.34 [+0.14, +0.52] † | +0.29 [+0.08, +0.50] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L6 · station=VIDP | ecmwf_ifs025 | 927 | -1.15 [-1.46, -0.86] † | +2.27 [+2.09, +2.43] | +2.76 [+2.57, +2.95] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L6 · station=VIDP | icon_global | 927 | -0.18 [-0.47, +0.10] | +1.93 [+1.78, +2.08] | +2.47 [+2.29, +2.66] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L6 · station=VOTR | difference: ecmwf_ifs025 minus icon_global | 930 | -1.77 [-1.95, -1.59] † | +1.00 [+0.86, +1.13] † | +0.96 [+0.80, +1.10] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L6 · station=VOTR | ecmwf_ifs025 | 930 | -2.44 [-2.63, -2.27] † | +2.61 [+2.46, +2.76] | +3.00 [+2.84, +3.14] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmax · L6 · station=VOTR | icon_global | 930 | -0.67 [-0.90, -0.46] † | +1.61 [+1.50, +1.74] | +2.04 [+1.92, +2.18] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L1 · station=VEIM | difference: ecmwf_ifs025 minus icon_global | 538 | +0.52 [+0.26, +0.78] † | -0.02 [-0.16, +0.11] | -0.10 [-0.25, +0.05] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L1 · station=VEIM | ecmwf_ifs025 | 538 | -0.22 [-0.48, +0.06] | +1.54 [+1.44, +1.65] | +1.81 [+1.69, +1.92] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L1 · station=VEIM | icon_global | 538 | -0.75 [-1.01, -0.48] † | +1.56 [+1.42, +1.70] | +1.91 [+1.76, +2.05] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L1 · station=VICG | difference: ecmwf_ifs025 minus icon_global | 139 | -1.23 [-1.42, -1.03] † | +0.23 [+0.03, +0.43] † | +0.06 [-0.20, +0.52] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L1 · station=VICG | ecmwf_ifs025 | 139 | -0.52 [-0.88, -0.14] † | +1.59 [+1.23, +1.99] | +2.75 [+1.65, +4.01] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L1 · station=VICG | icon_global | 139 | +0.71 [+0.31, +1.11] † | +1.36 [+1.05, +1.72] | +2.70 [+1.37, +4.14] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L1 · station=VIDP | difference: ecmwf_ifs025 minus icon_global | 932 | -1.01 [-1.12, -0.90] † | +0.56 [+0.47, +0.65] † | +0.54 [+0.44, +0.65] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L1 · station=VIDP | ecmwf_ifs025 | 932 | -1.44 [-1.57, -1.31] † | +1.74 [+1.64, +1.84] | +2.08 [+1.98, +2.18] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L1 · station=VIDP | icon_global | 932 | -0.44 [-0.58, -0.31] † | +1.18 [+1.10, +1.26] | +1.54 [+1.43, +1.65] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L1 · station=VOTR | difference: ecmwf_ifs025 minus icon_global | 935 | +0.05 [-0.08, +0.18] | -0.11 [-0.22, +0.01] | -0.10 [-0.22, +0.03] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L1 · station=VOTR | ecmwf_ifs025 | 935 | -1.36 [-1.48, -1.24] † | +1.53 [+1.45, +1.62] | +1.77 [+1.68, +1.86] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L1 · station=VOTR | icon_global | 935 | -1.41 [-1.53, -1.28] † | +1.64 [+1.55, +1.73] | +1.87 [+1.78, +1.96] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L2 · station=VEIM | difference: ecmwf_ifs025 minus icon_global | 541 | +0.59 [+0.36, +0.85] † | -0.05 [-0.19, +0.09] | -0.11 [-0.25, +0.06] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L2 · station=VEIM | ecmwf_ifs025 | 541 | -0.15 [-0.40, +0.15] | +1.53 [+1.43, +1.65] | +1.82 [+1.70, +1.94] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L2 · station=VEIM | icon_global | 541 | -0.74 [-0.99, -0.48] † | +1.59 [+1.46, +1.72] | +1.93 [+1.79, +2.06] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L2 · station=VICG | difference: ecmwf_ifs025 minus icon_global | 138 | -1.13 [-1.39, -0.84] † | +0.11 [-0.08, +0.29] | -0.05 [-0.23, +0.22] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L2 · station=VICG | ecmwf_ifs025 | 138 | -0.51 [-0.87, -0.09] † | +1.61 [+1.28, +2.06] | +2.71 [+1.63, +3.95] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L2 · station=VICG | icon_global | 138 | +0.62 [+0.20, +1.11] † | +1.50 [+1.17, +1.94] | +2.77 [+1.55, +4.12] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L2 · station=VIDP | difference: ecmwf_ifs025 minus icon_global | 935 | -0.95 [-1.09, -0.81] † | +0.53 [+0.43, +0.64] † | +0.54 [+0.42, +0.65] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L2 · station=VIDP | ecmwf_ifs025 | 935 | -1.48 [-1.64, -1.32] † | +1.82 [+1.71, +1.92] | +2.19 [+2.06, +2.30] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L2 · station=VIDP | icon_global | 935 | -0.53 [-0.68, -0.38] † | +1.29 [+1.21, +1.39] | +1.65 [+1.53, +1.77] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L2 · station=VOTR | difference: ecmwf_ifs025 minus icon_global | 938 | -0.02 [-0.15, +0.11] | -0.07 [-0.19, +0.04] | -0.07 [-0.20, +0.05] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L2 · station=VOTR | ecmwf_ifs025 | 938 | -1.42 [-1.54, -1.31] † | +1.59 [+1.51, +1.69] | +1.84 [+1.75, +1.93] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L2 · station=VOTR | icon_global | 938 | -1.40 [-1.53, -1.27] † | +1.66 [+1.58, +1.75] | +1.91 [+1.81, +2.00] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L3 · station=VEIM | difference: ecmwf_ifs025 minus icon_global | 537 | +0.65 [+0.41, +0.90] † | -0.09 [-0.23, +0.06] | -0.13 [-0.29, +0.05] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L3 · station=VEIM | ecmwf_ifs025 | 537 | -0.08 [-0.36, +0.21] | +1.49 [+1.38, +1.60] | +1.80 [+1.67, +1.93] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L3 · station=VEIM | icon_global | 537 | -0.72 [-1.00, -0.47] † | +1.58 [+1.44, +1.72] | +1.93 [+1.78, +2.07] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L3 · station=VICG | difference: ecmwf_ifs025 minus icon_global | 138 | -1.20 [-1.44, -0.96] † | +0.08 [-0.13, +0.26] | -0.02 [-0.15, +0.20] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L3 · station=VICG | ecmwf_ifs025 | 138 | -0.58 [-0.98, -0.13] † | +1.58 [+1.27, +2.01] | +2.71 [+1.64, +4.05] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L3 · station=VICG | icon_global | 138 | +0.62 [+0.17, +1.13] † | +1.51 [+1.17, +1.91] | +2.73 [+1.49, +4.17] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L3 · station=VIDP | difference: ecmwf_ifs025 minus icon_global | 930 | -0.95 [-1.08, -0.82] † | +0.54 [+0.44, +0.64] † | +0.50 [+0.40, +0.62] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L3 · station=VIDP | ecmwf_ifs025 | 930 | -1.50 [-1.67, -1.34] † | +1.91 [+1.80, +2.02] | +2.28 [+2.17, +2.40] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L3 · station=VIDP | icon_global | 930 | -0.55 [-0.70, -0.40] † | +1.37 [+1.28, +1.47] | +1.78 [+1.65, +1.91] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L3 · station=VOTR | difference: ecmwf_ifs025 minus icon_global | 933 | -0.09 [-0.23, +0.04] | +0.01 [-0.11, +0.13] | -0.02 [-0.15, +0.10] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L3 · station=VOTR | ecmwf_ifs025 | 933 | -1.45 [-1.57, -1.33] † | +1.63 [+1.55, +1.73] | +1.88 [+1.79, +1.97] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L3 · station=VOTR | icon_global | 933 | -1.35 [-1.50, -1.21] † | +1.63 [+1.54, +1.72] | +1.90 [+1.80, +2.00] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L4 · station=VEIM | difference: ecmwf_ifs025 minus icon_global | 537 | +0.77 [+0.50, +1.04] † | -0.13 [-0.29, +0.01] | -0.21 [-0.43, -0.02] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L4 · station=VEIM | ecmwf_ifs025 | 537 | -0.05 [-0.32, +0.23] | +1.52 [+1.40, +1.64] | +1.82 [+1.68, +1.95] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L4 · station=VEIM | icon_global | 537 | -0.82 [-1.11, -0.55] † | +1.65 [+1.51, +1.81] | +2.03 [+1.86, +2.22] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L4 · station=VICG | difference: ecmwf_ifs025 minus icon_global | 137 | -1.02 [-1.29, -0.80] † | +0.18 [+0.01, +0.35] † | -0.01 [-0.23, +0.31] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L4 · station=VICG | ecmwf_ifs025 | 137 | -0.32 [-0.73, +0.12] | +1.58 [+1.25, +2.02] | +2.73 [+1.64, +4.05] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L4 · station=VICG | icon_global | 137 | +0.70 [+0.30, +1.19] † | +1.40 [+1.05, +1.82] | +2.73 [+1.42, +4.22] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L4 · station=VIDP | difference: ecmwf_ifs025 minus icon_global | 929 | -0.99 [-1.14, -0.83] † | +0.54 [+0.43, +0.66] † | +0.53 [+0.40, +0.66] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L4 · station=VIDP | ecmwf_ifs025 | 929 | -1.45 [-1.64, -1.25] † | +1.93 [+1.81, +2.04] | +2.31 [+2.18, +2.42] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L4 · station=VIDP | icon_global | 929 | -0.47 [-0.64, -0.30] † | +1.39 [+1.29, +1.49] | +1.77 [+1.64, +1.90] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L4 · station=VOTR | difference: ecmwf_ifs025 minus icon_global | 932 | -0.09 [-0.21, +0.04] | +0.01 [-0.10, +0.12] | -0.02 [-0.13, +0.10] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L4 · station=VOTR | ecmwf_ifs025 | 932 | -1.42 [-1.54, -1.31] † | +1.62 [+1.54, +1.70] | +1.87 [+1.78, +1.95] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L4 · station=VOTR | icon_global | 932 | -1.34 [-1.48, -1.20] † | +1.61 [+1.52, +1.71] | +1.88 [+1.78, +1.99] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L5 · station=VEIM | difference: ecmwf_ifs025 minus icon_global | 537 | +0.76 [+0.48, +1.06] † | -0.15 [-0.31, +0.05] | -0.24 [-0.46, +0.02] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L5 · station=VEIM | ecmwf_ifs025 | 537 | -0.05 [-0.33, +0.26] | +1.56 [+1.45, +1.70] | +1.89 [+1.75, +2.05] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L5 · station=VEIM | icon_global | 537 | -0.81 [-1.08, -0.51] † | +1.71 [+1.54, +1.88] | +2.13 [+1.91, +2.33] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L5 · station=VICG | difference: ecmwf_ifs025 minus icon_global | 136 | -0.95 [-1.20, -0.66] † | +0.07 [-0.07, +0.25] | -0.07 [-0.31, +0.29] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L5 · station=VICG | ecmwf_ifs025 | 136 | -0.31 [-0.76, +0.22] | +1.51 [+1.13, +2.02] | +2.69 [+1.54, +4.01] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L5 · station=VICG | icon_global | 136 | +0.65 [+0.18, +1.20] † | +1.44 [+1.09, +1.90] | +2.75 [+1.42, +4.27] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L5 · station=VIDP | difference: ecmwf_ifs025 minus icon_global | 928 | -0.99 [-1.16, -0.81] † | +0.55 [+0.41, +0.67] † | +0.55 [+0.39, +0.70] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L5 · station=VIDP | ecmwf_ifs025 | 928 | -1.45 [-1.64, -1.25] † | +1.96 [+1.84, +2.08] | +2.37 [+2.24, +2.51] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L5 · station=VIDP | icon_global | 928 | -0.47 [-0.65, -0.28] † | +1.41 [+1.30, +1.52] | +1.82 [+1.66, +1.96] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L5 · station=VOTR | difference: ecmwf_ifs025 minus icon_global | 931 | -0.10 [-0.23, +0.03] | +0.03 [-0.08, +0.14] | +0.01 [-0.10, +0.13] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L5 · station=VOTR | ecmwf_ifs025 | 931 | -1.46 [-1.58, -1.35] † | +1.66 [+1.58, +1.75] | +1.91 [+1.82, +1.99] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L5 · station=VOTR | icon_global | 931 | -1.37 [-1.52, -1.24] † | +1.63 [+1.54, +1.73] | +1.90 [+1.80, +2.00] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L6 · station=VEIM | difference: ecmwf_ifs025 minus icon_global | 536 | +0.64 [+0.36, +0.94] † | -0.19 [-0.35, -0.03] † | -0.30 [-0.51, -0.11] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L6 · station=VEIM | ecmwf_ifs025 | 536 | -0.18 [-0.45, +0.12] | +1.54 [+1.41, +1.66] | +1.85 [+1.72, +1.98] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L6 · station=VEIM | icon_global | 536 | -0.82 [-1.12, -0.53] † | +1.72 [+1.56, +1.88] | +2.15 [+1.95, +2.33] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L6 · station=VICG | difference: ecmwf_ifs025 minus icon_global | 135 | -1.04 [-1.35, -0.72] † | +0.02 [-0.23, +0.22] | -0.07 [-0.34, +0.33] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L6 · station=VICG | ecmwf_ifs025 | 135 | -0.34 [-0.79, +0.17] | +1.59 [+1.17, +2.16] | +2.79 [+1.56, +4.22] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L6 · station=VICG | icon_global | 135 | +0.71 [+0.18, +1.32] † | +1.57 [+1.20, +2.09] | +2.86 [+1.55, +4.45] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L6 · station=VIDP | difference: ecmwf_ifs025 minus icon_global | 927 | -1.22 [-1.41, -1.05] † | +0.68 [+0.54, +0.81] † | +0.64 [+0.49, +0.80] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L6 · station=VIDP | ecmwf_ifs025 | 927 | -1.68 [-1.89, -1.46] † | +2.14 [+2.02, +2.27] | +2.56 [+2.41, +2.69] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L6 · station=VIDP | icon_global | 927 | -0.45 [-0.64, -0.26] † | +1.46 [+1.36, +1.58] | +1.92 [+1.78, +2.08] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L6 · station=VOTR | difference: ecmwf_ifs025 minus icon_global | 930 | -0.37 [-0.50, -0.24] † | +0.26 [+0.15, +0.37] † | +0.23 [+0.12, +0.34] † |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L6 · station=VOTR | ecmwf_ifs025 | 930 | -1.73 [-1.85, -1.61] † | +1.89 [+1.80, +1.98] | +2.13 [+2.05, +2.21] |
| A2 · shared-data:ecmwf_ifs025+icon_global · - · tmin · L6 · station=VOTR | icon_global | 930 | -1.36 [-1.49, -1.20] † | +1.63 [+1.53, +1.72] | +1.90 [+1.81, +2.00] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L1 · station=VEIM | difference: gfs_global minus icon_global | 538 | +2.57 [+2.17, +3.02] † | -0.11 [-0.46, +0.28] | -0.19 [-0.55, +0.21] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L1 · station=VEIM | gfs_global | 538 | +0.35 [-0.14, +0.87] | +2.46 [+2.24, +2.72] | +2.99 [+2.72, +3.28] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L1 · station=VEIM | icon_global | 538 | -2.22 [-2.57, -1.86] † | +2.57 [+2.30, +2.88] | +3.17 [+2.89, +3.48] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L1 · station=VICG | difference: gfs_global minus icon_global | 143 | +3.21 [+2.53, +3.88] † | +1.89 [+1.30, +2.45] † | +2.15 [+1.51, +2.73] † |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L1 · station=VICG | gfs_global | 143 | +3.07 [+2.40, +3.78] † | +3.29 [+2.70, +3.89] | +3.92 [+3.25, +4.56] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L1 · station=VICG | icon_global | 143 | -0.14 [-0.57, +0.25] | +1.40 [+1.21, +1.60] | +1.77 [+1.55, +1.97] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L1 · station=VIDP | difference: gfs_global minus icon_global | 936 | +3.62 [+3.37, +3.88] † | +1.98 [+1.78, +2.21] † | +2.13 [+1.92, +2.36] † |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L1 · station=VIDP | gfs_global | 936 | +3.20 [+2.97, +3.46] † | +3.26 [+3.03, +3.51] | +3.78 [+3.53, +4.07] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L1 · station=VIDP | icon_global | 936 | -0.42 [-0.56, -0.27] † | +1.28 [+1.18, +1.38] | +1.66 [+1.54, +1.77] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L1 · station=VOTR | difference: gfs_global minus icon_global | 939 | +0.03 [-0.15, +0.21] | +0.13 [-0.01, +0.27] | +0.25 [+0.08, +0.43] † |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L1 · station=VOTR | gfs_global | 939 | -1.37 [-1.57, -1.17] † | +1.75 [+1.59, +1.92] | +2.25 [+2.05, +2.47] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L1 · station=VOTR | icon_global | 939 | -1.40 [-1.54, -1.26] † | +1.62 [+1.50, +1.74] | +2.01 [+1.88, +2.14] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L2 · station=VEIM | difference: gfs_global minus icon_global | 541 | +2.55 [+2.13, +2.99] † | +0.01 [-0.34, +0.38] | -0.03 [-0.38, +0.36] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L2 · station=VEIM | gfs_global | 541 | +0.43 [-0.06, +0.93] | +2.58 [+2.34, +2.82] | +3.14 [+2.89, +3.42] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L2 · station=VEIM | icon_global | 541 | -2.12 [-2.49, -1.74] † | +2.57 [+2.29, +2.85] | +3.18 [+2.87, +3.45] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L2 · station=VICG | difference: gfs_global minus icon_global | 143 | +3.59 [+3.03, +4.25] † | +2.31 [+1.61, +2.99] † | +2.62 [+1.84, +3.35] † |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L2 · station=VICG | gfs_global | 143 | +3.36 [+2.63, +4.14] † | +3.70 [+3.00, +4.42] | +4.43 [+3.63, +5.20] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L2 · station=VICG | icon_global | 143 | -0.24 [-0.62, +0.19] | +1.39 [+1.21, +1.58] | +1.81 [+1.55, +2.07] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L2 · station=VIDP | difference: gfs_global minus icon_global | 940 | +3.95 [+3.67, +4.25] † | +2.07 [+1.84, +2.29] † | +2.22 [+1.97, +2.46] † |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L2 · station=VIDP | gfs_global | 940 | +3.48 [+3.23, +3.72] † | +3.54 [+3.30, +3.77] | +4.11 [+3.84, +4.39] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L2 · station=VIDP | icon_global | 940 | -0.47 [-0.66, -0.30] † | +1.47 [+1.36, +1.59] | +1.89 [+1.76, +2.04] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L2 · station=VOTR | difference: gfs_global minus icon_global | 943 | +0.02 [-0.19, +0.23] | +0.13 [-0.01, +0.29] | +0.27 [+0.09, +0.45] † |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L2 · station=VOTR | gfs_global | 943 | -1.19 [-1.41, -0.98] † | +1.70 [+1.54, +1.85] | +2.21 [+2.03, +2.40] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L2 · station=VOTR | icon_global | 943 | -1.21 [-1.37, -1.05] † | +1.57 [+1.44, +1.69] | +1.95 [+1.81, +2.08] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L3 · station=VEIM | difference: gfs_global minus icon_global | 538 | +2.50 [+2.05, +2.91] † | +0.16 [-0.23, +0.54] | +0.11 [-0.31, +0.52] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L3 · station=VEIM | gfs_global | 538 | +0.49 [-0.04, +0.99] | +2.64 [+2.41, +2.90] | +3.22 [+2.92, +3.52] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L3 · station=VEIM | icon_global | 538 | -2.01 [-2.39, -1.64] † | +2.48 [+2.20, +2.78] | +3.11 [+2.82, +3.42] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L3 · station=VICG | difference: gfs_global minus icon_global | 143 | +3.50 [+2.76, +4.24] † | +2.22 [+1.48, +2.91] † | +2.53 [+1.75, +3.18] † |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L3 · station=VICG | gfs_global | 143 | +3.33 [+2.52, +4.19] † | +3.68 [+2.93, +4.43] | +4.43 [+3.64, +5.14] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L3 · station=VICG | icon_global | 143 | -0.17 [-0.65, +0.28] | +1.45 [+1.26, +1.67] | +1.90 [+1.67, +2.13] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L3 · station=VIDP | difference: gfs_global minus icon_global | 936 | +3.92 [+3.64, +4.18] † | +2.09 [+1.86, +2.33] † | +2.26 [+1.99, +2.55] † |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L3 · station=VIDP | gfs_global | 936 | +3.54 [+3.27, +3.82] † | +3.64 [+3.36, +3.91] | +4.26 [+3.95, +4.58] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L3 · station=VIDP | icon_global | 936 | -0.38 [-0.58, -0.17] † | +1.55 [+1.42, +1.66] | +2.00 [+1.84, +2.15] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L3 · station=VOTR | difference: gfs_global minus icon_global | 939 | -0.06 [-0.27, +0.18] | +0.16 [+0.01, +0.29] † | +0.32 [+0.10, +0.52] † |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L3 · station=VOTR | gfs_global | 939 | -1.10 [-1.31, -0.86] † | +1.68 [+1.53, +1.83] | +2.21 [+1.99, +2.43] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L3 · station=VOTR | icon_global | 939 | -1.04 [-1.21, -0.86] † | +1.52 [+1.40, +1.63] | +1.89 [+1.76, +2.00] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L4 · station=VEIM | difference: gfs_global minus icon_global | 538 | +2.49 [+2.08, +2.92] † | +0.08 [-0.28, +0.45] | +0.02 [-0.35, +0.43] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L4 · station=VEIM | gfs_global | 538 | +0.45 [-0.06, +0.97] | +2.63 [+2.41, +2.85] | +3.21 [+2.98, +3.47] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L4 · station=VEIM | icon_global | 538 | -2.04 [-2.43, -1.66] † | +2.55 [+2.24, +2.85] | +3.19 [+2.87, +3.49] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L4 · station=VICG | difference: gfs_global minus icon_global | 143 | +3.46 [+2.59, +4.36] † | +2.06 [+1.37, +2.72] † | +2.40 [+1.64, +3.10] † |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L4 · station=VICG | gfs_global | 143 | +3.29 [+2.37, +4.20] † | +3.77 [+2.99, +4.48] | +4.55 [+3.75, +5.30] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L4 · station=VICG | icon_global | 143 | -0.17 [-0.67, +0.38] | +1.71 [+1.54, +1.89] | +2.16 [+1.97, +2.34] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L4 · station=VIDP | difference: gfs_global minus icon_global | 936 | +3.89 [+3.62, +4.16] † | +2.02 [+1.77, +2.27] † | +2.17 [+1.90, +2.46] † |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L4 · station=VIDP | gfs_global | 936 | +3.54 [+3.24, +3.85] † | +3.68 [+3.42, +3.98] | +4.35 [+4.03, +4.68] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L4 · station=VIDP | icon_global | 936 | -0.35 [-0.58, -0.12] † | +1.67 [+1.54, +1.82] | +2.18 [+2.01, +2.35] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L4 · station=VOTR | difference: gfs_global minus icon_global | 939 | -0.15 [-0.39, +0.10] | +0.21 [+0.07, +0.36] † | +0.41 [+0.20, +0.64] † |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L4 · station=VOTR | gfs_global | 939 | -1.05 [-1.31, -0.82] † | +1.76 [+1.59, +1.94] | +2.36 [+2.12, +2.61] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L4 · station=VOTR | icon_global | 939 | -0.91 [-1.09, -0.71] † | +1.55 [+1.42, +1.66] | +1.95 [+1.82, +2.07] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L5 · station=VEIM | difference: gfs_global minus icon_global | 538 | +2.43 [+2.02, +2.84] † | +0.17 [-0.16, +0.52] | +0.07 [-0.26, +0.42] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L5 · station=VEIM | gfs_global | 538 | +0.47 [-0.07, +0.98] | +2.76 [+2.55, +2.96] | +3.35 [+3.12, +3.59] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L5 · station=VEIM | icon_global | 538 | -1.96 [-2.35, -1.56] † | +2.59 [+2.29, +2.87] | +3.28 [+2.95, +3.57] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L5 · station=VICG | difference: gfs_global minus icon_global | 143 | +3.33 [+2.39, +4.27] † | +2.14 [+1.46, +2.88] † | +2.51 [+1.86, +3.16] † |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L5 · station=VICG | gfs_global | 143 | +3.40 [+2.46, +4.38] † | +3.90 [+3.13, +4.70] | +4.78 [+4.05, +5.48] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L5 · station=VICG | icon_global | 143 | +0.06 [-0.54, +0.58] | +1.77 [+1.49, +2.02] | +2.28 [+1.98, +2.54] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L5 · station=VIDP | difference: gfs_global minus icon_global | 936 | +3.80 [+3.54, +4.09] † | +1.88 [+1.63, +2.14] † | +2.08 [+1.81, +2.35] † |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L5 · station=VIDP | gfs_global | 936 | +3.52 [+3.22, +3.85] † | +3.70 [+3.42, +4.00] | +4.39 [+4.06, +4.73] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L5 · station=VIDP | icon_global | 936 | -0.29 [-0.54, -0.03] † | +1.81 [+1.68, +1.97] | +2.31 [+2.14, +2.49] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L5 · station=VOTR | difference: gfs_global minus icon_global | 939 | -0.40 [-0.63, -0.15] † | +0.23 [+0.08, +0.38] † | +0.40 [+0.20, +0.60] † |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L5 · station=VOTR | gfs_global | 939 | -1.12 [-1.37, -0.86] † | +1.83 [+1.65, +2.00] | +2.41 [+2.19, +2.62] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L5 · station=VOTR | icon_global | 939 | -0.72 [-0.94, -0.51] † | +1.60 [+1.48, +1.71] | +2.02 [+1.88, +2.16] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L6 · station=VEIM | difference: gfs_global minus icon_global | 538 | +2.25 [+1.86, +2.64] † | +0.34 [+0.03, +0.68] † | +0.35 [+0.03, +0.73] † |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L6 · station=VEIM | gfs_global | 538 | +0.47 [-0.06, +1.02] | +2.88 [+2.63, +3.11] | +3.52 [+3.25, +3.79] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L6 · station=VEIM | icon_global | 538 | -1.78 [-2.16, -1.38] † | +2.54 [+2.26, +2.80] | +3.17 [+2.89, +3.44] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L6 · station=VICG | difference: gfs_global minus icon_global | 143 | +3.40 [+2.42, +4.46] † | +1.96 [+1.25, +2.66] † | +2.22 [+1.53, +2.86] † |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L6 · station=VICG | gfs_global | 143 | +3.58 [+2.55, +4.66] † | +4.12 [+3.27, +5.00] | +5.03 [+4.20, +5.84] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L6 · station=VICG | icon_global | 143 | +0.18 [-0.59, +0.91] | +2.16 [+1.79, +2.58] | +2.81 [+2.39, +3.26] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L6 · station=VIDP | difference: gfs_global minus icon_global | 936 | +3.77 [+3.46, +4.07] † | +1.87 [+1.60, +2.12] † | +2.02 [+1.73, +2.29] † |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L6 · station=VIDP | gfs_global | 936 | +3.59 [+3.25, +3.90] † | +3.80 [+3.49, +4.08] | +4.49 [+4.13, +4.81] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L6 · station=VIDP | icon_global | 936 | -0.18 [-0.46, +0.12] | +1.93 [+1.79, +2.07] | +2.47 [+2.29, +2.64] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L6 · station=VOTR | difference: gfs_global minus icon_global | 939 | -0.46 [-0.72, -0.19] † | +0.25 [+0.10, +0.40] † | +0.44 [+0.22, +0.68] † |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L6 · station=VOTR | gfs_global | 939 | -1.10 [-1.35, -0.87] † | +1.86 [+1.70, +2.04] | +2.48 [+2.26, +2.71] |
| A2 · shared-data:gfs_global+icon_global · - · tmax · L6 · station=VOTR | icon_global | 939 | -0.65 [-0.85, -0.42] † | +1.61 [+1.50, +1.73] | +2.04 [+1.91, +2.17] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L1 · station=VEIM | difference: gfs_global minus icon_global | 538 | -1.05 [-1.25, -0.84] † | +0.38 [+0.22, +0.54] † | +0.35 [+0.19, +0.51] † |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L1 · station=VEIM | gfs_global | 538 | -1.79 [-1.97, -1.62] † | +1.94 [+1.81, +2.06] | +2.25 [+2.12, +2.38] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L1 · station=VEIM | icon_global | 538 | -0.75 [-1.01, -0.49] † | +1.56 [+1.43, +1.70] | +1.91 [+1.77, +2.04] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L1 · station=VICG | difference: gfs_global minus icon_global | 143 | +1.18 [+0.44, +1.89] † | +1.04 [+0.58, +1.47] † | +0.73 [+0.26, +1.48] † |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L1 · station=VICG | gfs_global | 143 | +1.86 [+1.11, +2.48] † | +2.40 [+1.86, +2.85] | +3.40 [+2.38, +4.47] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L1 · station=VICG | icon_global | 143 | +0.68 [+0.29, +1.12] † | +1.36 [+1.07, +1.70] | +2.67 [+1.38, +4.06] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L1 · station=VIDP | difference: gfs_global minus icon_global | 936 | +5.05 [+4.74, +5.38] † | +3.47 [+3.24, +3.72] † | +3.57 [+3.34, +3.81] † |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L1 · station=VIDP | gfs_global | 936 | +4.62 [+4.37, +4.90] † | +4.65 [+4.41, +4.91] | +5.11 [+4.88, +5.35] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L1 · station=VIDP | icon_global | 936 | -0.43 [-0.57, -0.30] † | +1.18 [+1.10, +1.27] | +1.54 [+1.43, +1.65] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L1 · station=VOTR | difference: gfs_global minus icon_global | 939 | +0.11 [-0.02, +0.25] | -0.03 [-0.13, +0.09] | +0.02 [-0.08, +0.13] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L1 · station=VOTR | gfs_global | 939 | -1.30 [-1.47, -1.12] † | +1.61 [+1.51, +1.72] | +1.88 [+1.79, +1.98] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L1 · station=VOTR | icon_global | 939 | -1.41 [-1.54, -1.27] † | +1.64 [+1.56, +1.73] | +1.87 [+1.78, +1.96] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L2 · station=VEIM | difference: gfs_global minus icon_global | 541 | -0.95 [-1.17, -0.74] † | +0.32 [+0.17, +0.47] † | +0.29 [+0.14, +0.45] † |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L2 · station=VEIM | gfs_global | 541 | -1.69 [-1.86, -1.50] † | +1.91 [+1.77, +2.03] | +2.22 [+2.09, +2.34] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L2 · station=VEIM | icon_global | 541 | -0.74 [-1.00, -0.46] † | +1.59 [+1.45, +1.72] | +1.93 [+1.78, +2.07] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L2 · station=VICG | difference: gfs_global minus icon_global | 143 | +1.40 [+0.64, +2.22] † | +1.10 [+0.64, +1.60] † | +0.96 [+0.54, +1.64] † |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L2 · station=VICG | gfs_global | 143 | +1.97 [+1.24, +2.73] † | +2.60 [+2.10, +3.10] | +3.69 [+2.72, +4.85] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L2 · station=VICG | icon_global | 143 | +0.57 [+0.11, +1.07] † | +1.50 [+1.17, +1.91] | +2.73 [+1.55, +4.10] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L2 · station=VIDP | difference: gfs_global minus icon_global | 940 | +5.28 [+4.96, +5.61] † | +3.50 [+3.22, +3.80] † | +3.65 [+3.37, +3.92] † |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L2 · station=VIDP | gfs_global | 940 | +4.76 [+4.45, +5.06] † | +4.79 [+4.50, +5.09] | +5.30 [+5.02, +5.58] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L2 · station=VIDP | icon_global | 940 | -0.52 [-0.67, -0.38] † | +1.29 [+1.21, +1.38] | +1.65 [+1.54, +1.77] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L2 · station=VOTR | difference: gfs_global minus icon_global | 943 | +0.13 [-0.03, +0.27] | -0.06 [-0.17, +0.05] | -0.01 [-0.12, +0.09] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L2 · station=VOTR | gfs_global | 943 | -1.27 [-1.44, -1.11] † | +1.60 [+1.50, +1.71] | +1.90 [+1.79, +1.99] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L2 · station=VOTR | icon_global | 943 | -1.40 [-1.54, -1.27] † | +1.67 [+1.58, +1.76] | +1.91 [+1.81, +2.00] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L3 · station=VEIM | difference: gfs_global minus icon_global | 538 | -0.88 [-1.12, -0.66] † | +0.30 [+0.15, +0.46] † | +0.27 [+0.11, +0.43] † |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L3 · station=VEIM | gfs_global | 538 | -1.60 [-1.79, -1.39] † | +1.88 [+1.75, +2.01] | +2.19 [+2.06, +2.31] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L3 · station=VEIM | icon_global | 538 | -0.72 [-1.00, -0.44] † | +1.58 [+1.43, +1.73] | +1.92 [+1.77, +2.07] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L3 · station=VICG | difference: gfs_global minus icon_global | 143 | +1.48 [+0.62, +2.33] † | +1.26 [+0.85, +1.69] † | +1.13 [+0.71, +1.77] † |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L3 · station=VICG | gfs_global | 143 | +2.03 [+1.24, +2.79] † | +2.76 [+2.26, +3.28] | +3.84 [+2.92, +4.97] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L3 · station=VICG | icon_global | 143 | +0.55 [+0.08, +1.07] † | +1.50 [+1.17, +1.91] | +2.71 [+1.51, +4.11] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L3 · station=VIDP | difference: gfs_global minus icon_global | 936 | +5.24 [+4.84, +5.58] † | +3.40 [+3.08, +3.71] † | +3.56 [+3.27, +3.84] † |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L3 · station=VIDP | gfs_global | 936 | +4.70 [+4.31, +5.05] † | +4.78 [+4.41, +5.10] | +5.33 [+5.01, +5.62] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L3 · station=VIDP | icon_global | 936 | -0.54 [-0.70, -0.38] † | +1.38 [+1.28, +1.48] | +1.78 [+1.65, +1.92] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L3 · station=VOTR | difference: gfs_global minus icon_global | 939 | +0.08 [-0.08, +0.23] | +0.02 [-0.11, +0.14] | +0.05 [-0.07, +0.18] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L3 · station=VOTR | gfs_global | 939 | -1.28 [-1.46, -1.10] † | +1.65 [+1.54, +1.75] | +1.95 [+1.84, +2.06] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L3 · station=VOTR | icon_global | 939 | -1.36 [-1.50, -1.22] † | +1.63 [+1.54, +1.73] | +1.90 [+1.80, +2.00] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L4 · station=VEIM | difference: gfs_global minus icon_global | 538 | -0.68 [-0.90, -0.45] † | +0.17 [+0.02, +0.32] † | +0.12 [-0.05, +0.29] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L4 · station=VEIM | gfs_global | 538 | -1.50 [-1.70, -1.30] † | +1.82 [+1.69, +1.95] | +2.15 [+2.02, +2.28] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L4 · station=VEIM | icon_global | 538 | -0.82 [-1.10, -0.55] † | +1.65 [+1.51, +1.79] | +2.03 [+1.85, +2.20] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L4 · station=VICG | difference: gfs_global minus icon_global | 143 | +1.24 [+0.44, +2.01] † | +1.29 [+0.82, +1.77] † | +1.12 [+0.67, +1.83] † |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L4 · station=VICG | gfs_global | 143 | +1.86 [+0.98, +2.72] † | +2.70 [+2.16, +3.26] | +3.83 [+2.83, +4.98] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L4 · station=VICG | icon_global | 143 | +0.63 [+0.17, +1.10] † | +1.40 [+1.08, +1.81] | +2.71 [+1.46, +4.12] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L4 · station=VIDP | difference: gfs_global minus icon_global | 936 | +5.12 [+4.73, +5.51] † | +3.37 [+3.03, +3.72] † | +3.58 [+3.29, +3.88] † |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L4 · station=VIDP | gfs_global | 936 | +4.66 [+4.28, +5.03] † | +4.75 [+4.41, +5.09] | +5.35 [+5.06, +5.66] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L4 · station=VIDP | icon_global | 936 | -0.46 [-0.63, -0.30] † | +1.38 [+1.29, +1.48] | +1.77 [+1.66, +1.90] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L4 · station=VOTR | difference: gfs_global minus icon_global | 939 | +0.05 [-0.12, +0.22] | +0.06 [-0.08, +0.20] | +0.11 [-0.04, +0.24] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L4 · station=VOTR | gfs_global | 939 | -1.29 [-1.46, -1.11] † | +1.67 [+1.56, +1.77] | +1.99 [+1.87, +2.10] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L4 · station=VOTR | icon_global | 939 | -1.34 [-1.48, -1.19] † | +1.61 [+1.52, +1.71] | +1.88 [+1.78, +1.98] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L5 · station=VEIM | difference: gfs_global minus icon_global | 538 | -0.74 [-1.00, -0.47] † | +0.15 [-0.02, +0.30] | +0.06 [-0.15, +0.24] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L5 · station=VEIM | gfs_global | 538 | -1.55 [-1.74, -1.35] † | +1.86 [+1.73, +2.00] | +2.18 [+2.05, +2.31] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L5 · station=VEIM | icon_global | 538 | -0.81 [-1.12, -0.52] † | +1.71 [+1.56, +1.89] | +2.13 [+1.93, +2.34] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L5 · station=VICG | difference: gfs_global minus icon_global | 143 | +1.44 [+0.59, +2.25] † | +1.26 [+0.82, +1.71] † | +1.08 [+0.61, +1.80] † |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L5 · station=VICG | gfs_global | 143 | +1.95 [+1.08, +2.80] † | +2.73 [+2.22, +3.27] | +3.84 [+2.84, +5.00] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L5 · station=VICG | icon_global | 143 | +0.51 [+0.02, +1.02] † | +1.47 [+1.14, +1.89] | +2.76 [+1.52, +4.26] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L5 · station=VIDP | difference: gfs_global minus icon_global | 936 | +5.28 [+4.88, +5.70] † | +3.51 [+3.14, +3.87] † | +3.74 [+3.42, +4.05] † |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L5 · station=VIDP | gfs_global | 936 | +4.82 [+4.42, +5.22] † | +4.92 [+4.55, +5.30] | +5.55 [+5.24, +5.88] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L5 · station=VIDP | icon_global | 936 | -0.46 [-0.66, -0.27] † | +1.41 [+1.32, +1.52] | +1.81 [+1.68, +1.97] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L5 · station=VOTR | difference: gfs_global minus icon_global | 939 | +0.05 [-0.11, +0.22] | +0.06 [-0.08, +0.19] | +0.12 [-0.02, +0.26] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L5 · station=VOTR | gfs_global | 939 | -1.31 [-1.48, -1.14] † | +1.68 [+1.57, +1.80] | +2.02 [+1.89, +2.13] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L5 · station=VOTR | icon_global | 939 | -1.37 [-1.50, -1.23] † | +1.63 [+1.53, +1.72] | +1.89 [+1.79, +1.99] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L6 · station=VEIM | difference: gfs_global minus icon_global | 538 | -0.69 [-0.94, -0.43] † | +0.14 [-0.02, +0.30] | +0.04 [-0.17, +0.22] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L6 · station=VEIM | gfs_global | 538 | -1.52 [-1.72, -1.33] † | +1.87 [+1.75, +2.01] | +2.19 [+2.07, +2.31] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L6 · station=VEIM | icon_global | 538 | -0.83 [-1.12, -0.51] † | +1.73 [+1.58, +1.89] | +2.16 [+1.97, +2.35] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L6 · station=VICG | difference: gfs_global minus icon_global | 143 | +1.44 [+0.62, +2.18] † | +1.13 [+0.72, +1.53] † | +1.08 [+0.66, +1.62] † |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L6 · station=VICG | gfs_global | 143 | +2.01 [+1.06, +2.87] † | +2.72 [+2.13, +3.30] | +3.91 [+2.79, +5.24] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L6 · station=VICG | icon_global | 143 | +0.57 [+0.02, +1.17] † | +1.59 [+1.25, +2.05] | +2.83 [+1.61, +4.31] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L6 · station=VIDP | difference: gfs_global minus icon_global | 936 | +5.29 [+4.87, +5.72] † | +3.50 [+3.17, +3.84] † | +3.66 [+3.37, +3.97] † |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L6 · station=VIDP | gfs_global | 936 | +4.84 [+4.45, +5.25] † | +4.96 [+4.61, +5.33] | +5.58 [+5.28, +5.90] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L6 · station=VIDP | icon_global | 936 | -0.45 [-0.63, -0.27] † | +1.46 [+1.36, +1.58] | +1.92 [+1.78, +2.07] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L6 · station=VOTR | difference: gfs_global minus icon_global | 939 | -0.02 [-0.19, +0.15] | +0.09 [-0.04, +0.22] | +0.16 [+0.03, +0.30] † |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L6 · station=VOTR | gfs_global | 939 | -1.38 [-1.56, -1.20] † | +1.71 [+1.59, +1.84] | +2.06 [+1.93, +2.19] |
| A2 · shared-data:gfs_global+icon_global · - · tmin · L6 · station=VOTR | icon_global | 939 | -1.36 [-1.50, -1.22] † | +1.63 [+1.54, +1.72] | +1.90 [+1.80, +2.00] |

## Primary — rain (08:30–08:30 IST) vs IMD (pooled, all seasons, all days, leads 1–6)

| Cell | Subject | n | Bias [95% CI] | MAE [95% CI] | RMSE [95% CI] |
| --- | --- | --- | --- | --- | --- |
| A3 · single-model · ecmwf_ifs025 · precip_0830 · L1 | ecmwf_ifs025 | 23,664 | -0.03 [-0.26, +0.18] | +4.51 [+3.72, +5.30] | +12.80 [+11.13, +14.50] |
| A3 · single-model · ecmwf_ifs025 · precip_0830 · L2 | ecmwf_ifs025 | 23,630 | +0.02 [-0.23, +0.23] | +4.64 [+3.82, +5.45] | +13.09 [+11.20, +14.67] |
| A3 · single-model · ecmwf_ifs025 · precip_0830 · L3 | ecmwf_ifs025 | 23,596 | +0.09 [-0.18, +0.34] | +4.89 [+4.10, +5.76] | +13.68 [+12.01, +15.35] |
| A3 · single-model · ecmwf_ifs025 · precip_0830 · L4 | ecmwf_ifs025 | 23,562 | -0.03 [-0.29, +0.21] | +5.01 [+4.13, +5.84] | +14.18 [+12.31, +15.96] |
| A3 · single-model · ecmwf_ifs025 · precip_0830 · L5 | ecmwf_ifs025 | 23,528 | +0.05 [-0.20, +0.32] | +5.16 [+4.29, +6.11] | +14.63 [+12.82, +16.44] |
| A3 · single-model · ecmwf_ifs025 · precip_0830 · L6 | ecmwf_ifs025 | 23,494 | +0.05 [-0.20, +0.31] | +5.23 [+4.32, +6.13] | +14.52 [+12.66, +16.42] |
| A3 · single-model · gfs_global · precip_0830 · L1 | gfs_global | 23,766 | -0.50 [-0.75, -0.26] † | +4.48 [+3.65, +5.28] | +13.41 [+11.41, +15.19] |
| A3 · single-model · gfs_global · precip_0830 · L2 | gfs_global | 23,766 | -0.51 [-0.73, -0.29] † | +4.67 [+3.82, +5.54] | +13.74 [+11.80, +15.51] |
| A3 · single-model · gfs_global · precip_0830 · L3 | gfs_global | 23,766 | -0.39 [-0.64, -0.13] † | +4.94 [+4.12, +5.81] | +14.19 [+12.43, +15.88] |
| A3 · single-model · gfs_global · precip_0830 · L4 | gfs_global | 23,766 | -0.22 [-0.50, +0.07] | +5.12 [+4.28, +6.04] | +14.78 [+13.03, +16.53] |
| A3 · single-model · gfs_global · precip_0830 · L5 | gfs_global | 23,766 | -2.68 [-3.31, -2.14] † | +4.35 [+3.59, +5.15] | +14.25 [+12.22, +16.19] |
| A3 · single-model · gfs_global · precip_0830 · L6 | gfs_global | 23,766 | -3.16 [-3.80, -2.49] † | +4.37 [+3.57, +5.14] | +14.51 [+12.33, +16.35] |
| A3 · single-model · icon_global · precip_0830 · L1 | icon_global | 23,766 | -0.45 [-0.68, -0.23] † | +4.57 [+3.76, +5.48] | +13.49 [+11.61, +15.43] |
| A3 · single-model · icon_global · precip_0830 · L2 | icon_global | 23,766 | -0.49 [-0.73, -0.23] † | +4.78 [+3.97, +5.66] | +14.13 [+12.29, +16.03] |
| A3 · single-model · icon_global · precip_0830 · L3 | icon_global | 23,766 | -0.58 [-0.86, -0.33] † | +4.83 [+3.99, +5.64] | +14.14 [+12.24, +15.77] |
| A3 · single-model · icon_global · precip_0830 · L4 | icon_global | 23,766 | -0.68 [-1.00, -0.36] † | +4.92 [+4.06, +5.76] | +14.38 [+12.66, +16.10] |
| A3 · single-model · icon_global · precip_0830 · L5 | icon_global | 23,766 | -0.59 [-0.93, -0.26] † | +5.09 [+4.22, +6.03] | +14.95 [+12.91, +16.87] |
| A3 · single-model · icon_global · precip_0830 · L6 | icon_global | 23,766 | -0.58 [-0.89, -0.27] † | +5.20 [+4.28, +6.15] | +15.38 [+13.40, +17.40] |

Model pairs on shared data:

| Cell | Subject | n | Bias [95% CI] | MAE [95% CI] | RMSE [95% CI] |
| --- | --- | --- | --- | --- | --- |
| A3 · shared-data:ecmwf_ifs025+gfs_global · - · precip_0830 · L1 | difference: ecmwf_ifs025 minus gfs_global | 23,664 | +0.47 [+0.32, +0.61] † | +0.02 [-0.11, +0.13] | -0.64 [-1.07, -0.22] † |
| A3 · shared-data:ecmwf_ifs025+gfs_global · - · precip_0830 · L1 | ecmwf_ifs025 | 23,664 | -0.03 [-0.26, +0.17] | +4.51 [+3.81, +5.38] | +12.80 [+11.22, +14.48] |
| A3 · shared-data:ecmwf_ifs025+gfs_global · - · precip_0830 · L1 | gfs_global | 23,664 | -0.50 [-0.75, -0.28] † | +4.49 [+3.74, +5.40] | +13.44 [+11.73, +15.32] |
| A3 · shared-data:ecmwf_ifs025+gfs_global · - · precip_0830 · L2 | difference: ecmwf_ifs025 minus gfs_global | 23,630 | +0.53 [+0.34, +0.72] † | -0.05 [-0.17, +0.07] | -0.69 [-1.13, -0.20] † |
| A3 · shared-data:ecmwf_ifs025+gfs_global · - · precip_0830 · L2 | ecmwf_ifs025 | 23,630 | +0.02 [-0.22, +0.26] | +4.64 [+3.84, +5.43] | +13.09 [+11.33, +14.77] |
| A3 · shared-data:ecmwf_ifs025+gfs_global · - · precip_0830 · L2 | gfs_global | 23,630 | -0.51 [-0.72, -0.29] † | +4.69 [+3.86, +5.51] | +13.78 [+11.92, +15.53] |
| A3 · shared-data:ecmwf_ifs025+gfs_global · - · precip_0830 · L3 | difference: ecmwf_ifs025 minus gfs_global | 23,596 | +0.48 [+0.28, +0.68] † | -0.08 [-0.24, +0.06] | -0.55 [-0.99, -0.08] † |
| A3 · shared-data:ecmwf_ifs025+gfs_global · - · precip_0830 · L3 | ecmwf_ifs025 | 23,596 | +0.09 [-0.17, +0.33] | +4.89 [+4.09, +5.73] | +13.68 [+12.04, +15.28] |
| A3 · shared-data:ecmwf_ifs025+gfs_global · - · precip_0830 · L3 | gfs_global | 23,596 | -0.39 [-0.65, -0.15] † | +4.97 [+4.14, +5.88] | +14.24 [+12.52, +15.98] |
| A3 · shared-data:ecmwf_ifs025+gfs_global · - · precip_0830 · L4 | difference: ecmwf_ifs025 minus gfs_global | 23,562 | +0.19 [+0.00, +0.38] † | -0.14 [-0.30, +0.02] | -0.66 [-1.10, -0.22] † |
| A3 · shared-data:ecmwf_ifs025+gfs_global · - · precip_0830 · L4 | ecmwf_ifs025 | 23,562 | -0.03 [-0.31, +0.23] | +5.01 [+4.11, +5.89] | +14.18 [+12.36, +15.90] |
| A3 · shared-data:ecmwf_ifs025+gfs_global · - · precip_0830 · L4 | gfs_global | 23,562 | -0.22 [-0.48, +0.03] | +5.15 [+4.22, +6.08] | +14.84 [+12.86, +16.65] |
| A3 · shared-data:ecmwf_ifs025+gfs_global · - · precip_0830 · L5 | difference: ecmwf_ifs025 minus gfs_global | 23,528 | +2.76 [+2.23, +3.30] † | +0.78 [+0.61, +0.97] † | +0.31 [-0.07, +0.75] |
| A3 · shared-data:ecmwf_ifs025+gfs_global · - · precip_0830 · L5 | ecmwf_ifs025 | 23,528 | +0.05 [-0.21, +0.32] | +5.16 [+4.28, +6.08] | +14.63 [+12.74, +16.44] |
| A3 · shared-data:ecmwf_ifs025+gfs_global · - · precip_0830 · L5 | gfs_global | 23,528 | -2.70 [-3.32, -2.16] † | +4.38 [+3.61, +5.21] | +14.32 [+12.33, +16.26] |
| A3 · shared-data:ecmwf_ifs025+gfs_global · - · precip_0830 · L6 | difference: ecmwf_ifs025 minus gfs_global | 23,494 | +3.24 [+2.68, +3.87] † | +0.82 [+0.67, +0.98] † | -0.07 [-0.34, +0.20] |
| A3 · shared-data:ecmwf_ifs025+gfs_global · - · precip_0830 · L6 | ecmwf_ifs025 | 23,494 | +0.05 [-0.21, +0.29] | +5.23 [+4.38, +6.16] | +14.52 [+12.58, +16.39] |
| A3 · shared-data:ecmwf_ifs025+gfs_global · - · precip_0830 · L6 | gfs_global | 23,494 | -3.19 [-3.85, -2.57] † | +4.41 [+3.64, +5.22] | +14.59 [+12.49, +16.62] |
| A3 · shared-data:ecmwf_ifs025+icon_global · - · precip_0830 · L1 | difference: ecmwf_ifs025 minus icon_global | 23,664 | +0.42 [+0.25, +0.58] † | -0.08 [-0.22, +0.04] | -0.72 [-1.15, -0.31] † |
| A3 · shared-data:ecmwf_ifs025+icon_global · - · precip_0830 · L1 | ecmwf_ifs025 | 23,664 | -0.03 [-0.26, +0.18] | +4.51 [+3.77, +5.32] | +12.80 [+11.15, +14.53] |
| A3 · shared-data:ecmwf_ifs025+icon_global · - · precip_0830 · L1 | icon_global | 23,664 | -0.45 [-0.69, -0.23] † | +4.59 [+3.81, +5.46] | +13.51 [+11.65, +15.49] |
| A3 · shared-data:ecmwf_ifs025+icon_global · - · precip_0830 · L2 | difference: ecmwf_ifs025 minus icon_global | 23,630 | +0.51 [+0.32, +0.68] † | -0.15 [-0.29, -0.03] † | -1.07 [-1.65, -0.55] † |
| A3 · shared-data:ecmwf_ifs025+icon_global · - · precip_0830 · L2 | ecmwf_ifs025 | 23,630 | +0.02 [-0.22, +0.23] | +4.64 [+3.86, +5.48] | +13.09 [+11.30, +14.95] |
| A3 · shared-data:ecmwf_ifs025+icon_global · - · precip_0830 · L2 | icon_global | 23,630 | -0.49 [-0.77, -0.25] † | +4.80 [+3.96, +5.70] | +14.16 [+12.26, +16.24] |
| A3 · shared-data:ecmwf_ifs025+icon_global · - · precip_0830 · L3 | difference: ecmwf_ifs025 minus icon_global | 23,596 | +0.68 [+0.46, +0.90] † | +0.03 [-0.09, +0.17] | -0.50 [-0.96, -0.00] † |
| A3 · shared-data:ecmwf_ifs025+icon_global · - · precip_0830 · L3 | ecmwf_ifs025 | 23,596 | +0.09 [-0.16, +0.33] | +4.89 [+4.03, +5.76] | +13.68 [+11.86, +15.34] |
| A3 · shared-data:ecmwf_ifs025+icon_global · - · precip_0830 · L3 | icon_global | 23,596 | -0.59 [-0.87, -0.32] † | +4.85 [+3.95, +5.72] | +14.18 [+12.20, +15.97] |
| A3 · shared-data:ecmwf_ifs025+icon_global · - · precip_0830 · L4 | difference: ecmwf_ifs025 minus icon_global | 23,562 | +0.66 [+0.43, +0.89] † | +0.06 [-0.08, +0.20] | -0.26 [-0.75, +0.28] |
| A3 · shared-data:ecmwf_ifs025+icon_global · - · precip_0830 · L4 | ecmwf_ifs025 | 23,562 | -0.03 [-0.30, +0.22] | +5.01 [+4.11, +5.85] | +14.18 [+12.35, +16.00] |
| A3 · shared-data:ecmwf_ifs025+icon_global · - · precip_0830 · L4 | icon_global | 23,562 | -0.69 [-1.04, -0.37] † | +4.95 [+4.08, +5.82] | +14.44 [+12.50, +16.28] |
| A3 · shared-data:ecmwf_ifs025+icon_global · - · precip_0830 · L5 | difference: ecmwf_ifs025 minus icon_global | 23,528 | +0.65 [+0.39, +0.92] † | +0.03 [-0.14, +0.20] | -0.39 [-1.13, +0.27] |
| A3 · shared-data:ecmwf_ifs025+icon_global · - · precip_0830 · L5 | ecmwf_ifs025 | 23,528 | +0.05 [-0.20, +0.32] | +5.16 [+4.22, +6.15] | +14.63 [+12.74, +16.53] |
| A3 · shared-data:ecmwf_ifs025+icon_global · - · precip_0830 · L5 | icon_global | 23,528 | -0.60 [-0.92, -0.29] † | +5.13 [+4.21, +6.13] | +15.02 [+13.02, +16.88] |
| A3 · shared-data:ecmwf_ifs025+icon_global · - · precip_0830 · L6 | difference: ecmwf_ifs025 minus icon_global | 23,494 | +0.64 [+0.37, +0.91] † | -0.02 [-0.18, +0.14] | -0.94 [-1.60, -0.38] † |
| A3 · shared-data:ecmwf_ifs025+icon_global · - · precip_0830 · L6 | ecmwf_ifs025 | 23,494 | +0.05 [-0.19, +0.29] | +5.23 [+4.36, +6.16] | +14.52 [+12.60, +16.35] |
| A3 · shared-data:ecmwf_ifs025+icon_global · - · precip_0830 · L6 | icon_global | 23,494 | -0.59 [-0.92, -0.27] † | +5.25 [+4.36, +6.18] | +15.46 [+13.40, +17.44] |
| A3 · shared-data:gfs_global+icon_global · - · precip_0830 · L1 | difference: gfs_global minus icon_global | 23,766 | -0.06 [-0.24, +0.13] | -0.10 [-0.23, +0.03] | -0.08 [-0.51, +0.40] |
| A3 · shared-data:gfs_global+icon_global · - · precip_0830 · L1 | gfs_global | 23,766 | -0.50 [-0.73, -0.26] † | +4.48 [+3.68, +5.33] | +13.41 [+11.46, +15.17] |
| A3 · shared-data:gfs_global+icon_global · - · precip_0830 · L1 | icon_global | 23,766 | -0.45 [-0.68, -0.22] † | +4.57 [+3.75, +5.47] | +13.49 [+11.44, +15.33] |
| A3 · shared-data:gfs_global+icon_global · - · precip_0830 · L2 | difference: gfs_global minus icon_global | 23,766 | -0.02 [-0.21, +0.17] | -0.11 [-0.25, +0.04] | -0.38 [-0.88, +0.14] |
| A3 · shared-data:gfs_global+icon_global · - · precip_0830 · L2 | gfs_global | 23,766 | -0.51 [-0.75, -0.28] † | +4.67 [+3.86, +5.55] | +13.74 [+11.98, +15.80] |
| A3 · shared-data:gfs_global+icon_global · - · precip_0830 · L2 | icon_global | 23,766 | -0.49 [-0.75, -0.26] † | +4.78 [+3.94, +5.65] | +14.13 [+12.21, +16.09] |
| A3 · shared-data:gfs_global+icon_global · - · precip_0830 · L3 | difference: gfs_global minus icon_global | 23,766 | +0.19 [-0.07, +0.45] | +0.12 [-0.05, +0.29] | +0.05 [-0.62, +0.73] |
| A3 · shared-data:gfs_global+icon_global · - · precip_0830 · L3 | gfs_global | 23,766 | -0.39 [-0.65, -0.17] † | +4.94 [+4.11, +5.82] | +14.19 [+12.35, +15.84] |
| A3 · shared-data:gfs_global+icon_global · - · precip_0830 · L3 | icon_global | 23,766 | -0.58 [-0.85, -0.32] † | +4.83 [+4.01, +5.70] | +14.14 [+12.35, +15.86] |
| A3 · shared-data:gfs_global+icon_global · - · precip_0830 · L4 | difference: gfs_global minus icon_global | 23,766 | +0.46 [+0.20, +0.76] † | +0.19 [+0.04, +0.37] † | +0.40 [-0.10, +0.90] |
| A3 · shared-data:gfs_global+icon_global · - · precip_0830 · L4 | gfs_global | 23,766 | -0.22 [-0.49, +0.04] | +5.12 [+4.17, +6.09] | +14.78 [+12.91, +16.67] |
| A3 · shared-data:gfs_global+icon_global · - · precip_0830 · L4 | icon_global | 23,766 | -0.68 [-1.02, -0.38] † | +4.92 [+4.04, +5.83] | +14.38 [+12.59, +16.25] |
| A3 · shared-data:gfs_global+icon_global · - · precip_0830 · L5 | difference: gfs_global minus icon_global | 23,766 | -2.09 [-2.49, -1.72] † | -0.74 [-0.92, -0.58] † | -0.70 [-1.49, +0.02] |
| A3 · shared-data:gfs_global+icon_global · - · precip_0830 · L5 | gfs_global | 23,766 | -2.68 [-3.25, -2.11] † | +4.35 [+3.55, +5.11] | +14.25 [+12.30, +16.25] |
| A3 · shared-data:gfs_global+icon_global · - · precip_0830 · L5 | icon_global | 23,766 | -0.59 [-0.92, -0.27] † | +5.09 [+4.23, +5.94] | +14.95 [+13.13, +16.90] |
| A3 · shared-data:gfs_global+icon_global · - · precip_0830 · L6 | difference: gfs_global minus icon_global | 23,766 | -2.58 [-3.04, -2.10] † | -0.84 [-1.05, -0.64] † | -0.87 [-1.70, -0.17] † |
| A3 · shared-data:gfs_global+icon_global · - · precip_0830 · L6 | gfs_global | 23,766 | -3.16 [-3.81, -2.57] † | +4.37 [+3.62, +5.15] | +14.51 [+12.52, +16.57] |
| A3 · shared-data:gfs_global+icon_global · - · precip_0830 · L6 | icon_global | 23,766 | -0.58 [-0.92, -0.27] † | +5.20 [+4.33, +6.08] | +15.38 [+13.36, +17.35] |

## Exploratory (not findings)

9,261 cells. Full values in metric_results.csv. Pooled, all-season, single-model summary below; seasonal, regional, elevation, rainy-day, lead-7 and three-model cells are in the CSV.

| Cell | Subject | n | Bias [95% CI] | MAE [95% CI] | RMSE [95% CI] |
| --- | --- | --- | --- | --- | --- |
| A1 · single-model · ecmwf_ifs025 · tmax · L1 | ecmwf_ifs025 | 33,804 | -0.57 [-0.63, -0.50] † | +1.38 [+1.36, +1.41] | +1.75 [+1.72, +1.79] |
| A1 · single-model · ecmwf_ifs025 · tmax · L2 | ecmwf_ifs025 | 33,768 | -0.49 [-0.57, -0.42] † | +1.43 [+1.41, +1.46] | +1.83 [+1.79, +1.86] |
| A1 · single-model · ecmwf_ifs025 · tmax · L3 | ecmwf_ifs025 | 33,732 | -0.39 [-0.48, -0.30] † | +1.47 [+1.45, +1.51] | +1.90 [+1.86, +1.94] |
| A1 · single-model · ecmwf_ifs025 · tmax · L4 | ecmwf_ifs025 | 33,696 | -0.31 [-0.42, -0.21] † | +1.52 [+1.49, +1.56] | +1.97 [+1.92, +2.02] |
| A1 · single-model · ecmwf_ifs025 · tmax · L5 | ecmwf_ifs025 | 33,660 | -0.26 [-0.35, -0.16] † | +1.58 [+1.54, +1.61] | +2.04 [+1.99, +2.09] |
| A1 · single-model · ecmwf_ifs025 · tmax · L6 | ecmwf_ifs025 | 33,624 | -0.82 [-0.93, -0.71] † | +1.82 [+1.79, +1.86] | +2.31 [+2.26, +2.36] |
| A1 · single-model · ecmwf_ifs025 · tmax · L7 | ecmwf_ifs025 | 33,588 | -0.76 [-0.87, -0.63] † | +1.86 [+1.82, +1.91] | +2.37 [+2.32, +2.42] |
| A1 · single-model · ecmwf_ifs025 · tmin · L1 | ecmwf_ifs025 | 33,804 | -1.27 [-1.31, -1.22] † | +1.60 [+1.57, +1.63] | +2.11 [+2.06, +2.15] |
| A1 · single-model · ecmwf_ifs025 · tmin · L2 | ecmwf_ifs025 | 33,768 | -1.26 [-1.31, -1.21] † | +1.64 [+1.61, +1.67] | +2.15 [+2.10, +2.19] |
| A1 · single-model · ecmwf_ifs025 · tmin · L3 | ecmwf_ifs025 | 33,732 | -1.25 [-1.29, -1.19] † | +1.66 [+1.63, +1.69] | +2.18 [+2.13, +2.23] |
| A1 · single-model · ecmwf_ifs025 · tmin · L4 | ecmwf_ifs025 | 33,696 | -1.23 [-1.28, -1.17] † | +1.68 [+1.65, +1.72] | +2.21 [+2.16, +2.26] |
| A1 · single-model · ecmwf_ifs025 · tmin · L5 | ecmwf_ifs025 | 33,660 | -1.22 [-1.27, -1.16] † | +1.70 [+1.66, +1.74] | +2.23 [+2.18, +2.29] |
| A1 · single-model · ecmwf_ifs025 · tmin · L6 | ecmwf_ifs025 | 33,624 | -1.39 [-1.45, -1.32] † | +1.85 [+1.80, +1.89] | +2.39 [+2.31, +2.45] |
| A1 · single-model · ecmwf_ifs025 · tmin · L7 | ecmwf_ifs025 | 33,588 | -1.37 [-1.44, -1.31] † | +1.87 [+1.82, +1.92] | +2.41 [+2.35, +2.48] |
| A1 · single-model · gfs_global · tmax · L1 | gfs_global | 33,948 | +1.02 [+0.85, +1.19] † | +1.98 [+1.89, +2.06] | +2.59 [+2.47, +2.69] |
| A1 · single-model · gfs_global · tmax · L2 | gfs_global | 33,948 | +1.15 [+0.94, +1.37] † | +2.14 [+2.04, +2.24] | +2.79 [+2.68, +2.91] |
| A1 · single-model · gfs_global · tmax · L3 | gfs_global | 33,948 | +1.23 [+1.01, +1.43] † | +2.24 [+2.14, +2.35] | +2.93 [+2.80, +3.05] |
| A1 · single-model · gfs_global · tmax · L4 | gfs_global | 33,948 | +1.28 [+1.08, +1.50] † | +2.31 [+2.22, +2.42] | +3.02 [+2.90, +3.14] |
| A1 · single-model · gfs_global · tmax · L5 | gfs_global | 33,948 | +1.24 [+1.01, +1.46] † | +2.36 [+2.25, +2.46] | +3.08 [+2.94, +3.20] |
| A1 · single-model · gfs_global · tmax · L6 | gfs_global | 33,948 | +1.27 [+1.05, +1.50] † | +2.44 [+2.33, +2.55] | +3.18 [+3.05, +3.30] |
| A1 · single-model · gfs_global · tmax · L7 | gfs_global | 33,948 | +1.32 [+1.09, +1.55] † | +2.48 [+2.38, +2.59] | +3.24 [+3.12, +3.37] |
| A1 · single-model · gfs_global · tmin · L1 | gfs_global | 33,948 | -0.23 [-0.33, -0.14] † | +1.71 [+1.66, +1.76] | +2.21 [+2.14, +2.28] |
| A1 · single-model · gfs_global · tmin · L2 | gfs_global | 33,948 | -0.17 [-0.27, -0.07] † | +1.77 [+1.73, +1.82] | +2.29 [+2.22, +2.35] |
| A1 · single-model · gfs_global · tmin · L3 | gfs_global | 33,948 | -0.13 [-0.24, -0.02] † | +1.83 [+1.78, +1.88] | +2.35 [+2.28, +2.42] |
| A1 · single-model · gfs_global · tmin · L4 | gfs_global | 33,948 | -0.12 [-0.24, -0.01] † | +1.86 [+1.81, +1.91] | +2.39 [+2.32, +2.46] |
| A1 · single-model · gfs_global · tmin · L5 | gfs_global | 33,948 | -0.13 [-0.25, -0.01] † | +1.92 [+1.87, +1.97] | +2.46 [+2.39, +2.54] |
| A1 · single-model · gfs_global · tmin · L6 | gfs_global | 33,948 | -0.13 [-0.25, -0.00] † | +1.95 [+1.89, +2.01] | +2.51 [+2.43, +2.59] |
| A1 · single-model · gfs_global · tmin · L7 | gfs_global | 33,948 | -0.14 [-0.26, -0.02] † | +1.96 [+1.90, +2.02] | +2.53 [+2.44, +2.61] |
| A1 · single-model · icon_global · tmax · L1 | icon_global | 33,804 | -0.37 [-0.46, -0.26] † | +1.51 [+1.47, +1.55] | +2.07 [+2.01, +2.13] |
| A1 · single-model · icon_global · tmax · L2 | icon_global | 33,948 | -0.31 [-0.42, -0.21] † | +1.62 [+1.58, +1.65] | +2.19 [+2.13, +2.25] |
| A1 · single-model · icon_global · tmax · L3 | icon_global | 33,804 | -0.22 [-0.33, -0.10] † | +1.67 [+1.63, +1.71] | +2.26 [+2.20, +2.32] |
| A1 · single-model · icon_global · tmax · L4 | icon_global | 33,804 | -0.19 [-0.31, -0.07] † | +1.74 [+1.70, +1.79] | +2.34 [+2.28, +2.40] |
| A1 · single-model · icon_global · tmax · L5 | icon_global | 33,804 | -0.14 [-0.27, -0.01] † | +1.85 [+1.80, +1.90] | +2.48 [+2.41, +2.54] |
| A1 · single-model · icon_global · tmax · L6 | icon_global | 33,804 | -0.06 [-0.20, +0.08] | +1.92 [+1.87, +1.98] | +2.57 [+2.49, +2.64] |
| A1 · single-model · icon_global · tmin · L1 | icon_global | 33,804 | -0.47 [-0.52, -0.42] † | +1.40 [+1.34, +1.45] | +1.95 [+1.87, +2.02] |
| A1 · single-model · icon_global · tmin · L2 | icon_global | 33,948 | -0.50 [-0.57, -0.44] † | +1.46 [+1.40, +1.52] | +2.01 [+1.93, +2.09] |
| A1 · single-model · icon_global · tmin · L3 | icon_global | 33,804 | -0.50 [-0.57, -0.43] † | +1.49 [+1.43, +1.55] | +2.04 [+1.96, +2.12] |
| A1 · single-model · icon_global · tmin · L4 | icon_global | 33,804 | -0.50 [-0.57, -0.42] † | +1.53 [+1.47, +1.59] | +2.08 [+2.00, +2.17] |
| A1 · single-model · icon_global · tmin · L5 | icon_global | 33,804 | -0.50 [-0.57, -0.43] † | +1.56 [+1.50, +1.62] | +2.12 [+2.04, +2.20] |
| A1 · single-model · icon_global · tmin · L6 | icon_global | 33,804 | -0.50 [-0.57, -0.42] † | +1.59 [+1.52, +1.65] | +2.16 [+2.07, +2.24] |
| A3 · single-model · ecmwf_ifs025 · precip_0830 · L7 | ecmwf_ifs025 | 23,460 | +0.08 [-0.17, +0.33] | +5.26 [+4.39, +6.20] | +14.42 [+12.62, +16.16] |
| A3 · single-model · gfs_global · precip_0830 · L7 | gfs_global | 23,766 | -3.18 [-3.88, -2.58] † | +4.39 [+3.64, +5.23] | +14.54 [+12.65, +16.46] |
| A4 · single-model · ecmwf_ifs025 · precip · L1 | ecmwf_ifs025 | 33,804 | -0.02 [-0.15, +0.09] | +3.28 [+2.86, +3.78] | +8.80 [+7.84, +9.85] |
| A4 · single-model · ecmwf_ifs025 · precip · L2 | ecmwf_ifs025 | 33,768 | +0.07 [-0.06, +0.20] | +3.56 [+3.11, +4.09] | +9.47 [+8.41, +10.49] |
| A4 · single-model · ecmwf_ifs025 · precip · L3 | ecmwf_ifs025 | 33,732 | +0.12 [-0.03, +0.27] | +3.86 [+3.32, +4.43] | +10.38 [+9.10, +11.81] |
| A4 · single-model · ecmwf_ifs025 · precip · L4 | ecmwf_ifs025 | 33,696 | -0.03 [-0.19, +0.13] | +3.98 [+3.47, +4.56] | +10.96 [+9.54, +12.52] |
| A4 · single-model · ecmwf_ifs025 · precip · L5 | ecmwf_ifs025 | 33,408 | +0.03 [-0.14, +0.21] | +4.18 [+3.54, +4.79] | +10.97 [+9.73, +12.04] |
| A4 · single-model · ecmwf_ifs025 · precip · L6 | ecmwf_ifs025 | 33,624 | +0.00 [-0.17, +0.18] | +4.26 [+3.69, +4.86] | +11.00 [+9.84, +12.17] |
| A4 · single-model · ecmwf_ifs025 · precip · L7 | ecmwf_ifs025 | 33,336 | +0.04 [-0.12, +0.23] | +4.36 [+3.83, +4.99] | +11.16 [+10.18, +12.19] |
| A4 · single-model · gfs_global · precip · L1 | gfs_global | 33,948 | -0.57 [-0.71, -0.43] † | +3.78 [+3.23, +4.30] | +10.42 [+9.24, +11.47] |
| A4 · single-model · gfs_global · precip · L2 | gfs_global | 33,948 | -0.57 [-0.73, -0.43] † | +4.01 [+3.43, +4.65] | +10.87 [+9.55, +12.27] |
| A4 · single-model · gfs_global · precip · L3 | gfs_global | 33,948 | -0.48 [-0.66, -0.31] † | +4.24 [+3.67, +4.87] | +11.33 [+10.13, +12.59] |
| A4 · single-model · gfs_global · precip · L4 | gfs_global | 33,948 | -0.30 [-0.48, -0.13] † | +4.46 [+3.86, +5.15] | +12.00 [+10.77, +13.27] |
| A4 · single-model · gfs_global · precip · L5 | gfs_global | 33,948 | -2.59 [-3.07, -2.17] † | +3.95 [+3.40, +4.57] | +11.06 [+9.80, +12.43] |
| A4 · single-model · gfs_global · precip · L6 | gfs_global | 33,948 | -3.03 [-3.56, -2.56] † | +4.07 [+3.53, +4.66] | +11.42 [+10.17, +12.67] |
| A4 · single-model · gfs_global · precip · L7 | gfs_global | 33,948 | -3.04 [-3.61, -2.55] † | +4.10 [+3.51, +4.74] | +11.39 [+10.15, +12.67] |
| A4 · single-model · icon_global · precip · L1 | icon_global | 33,804 | -0.50 [-0.65, -0.34] † | +3.70 [+3.19, +4.27] | +10.12 [+8.98, +11.29] |
| A4 · single-model · icon_global · precip · L2 | icon_global | 33,804 | -0.54 [-0.73, -0.40] † | +3.89 [+3.35, +4.51] | +10.87 [+9.47, +12.38] |
| A4 · single-model · icon_global · precip · L3 | icon_global | 33,948 | -0.67 [-0.86, -0.48] † | +4.02 [+3.48, +4.61] | +11.47 [+9.87, +13.21] |
| A4 · single-model · icon_global · precip · L4 | icon_global | 33,948 | -0.79 [-1.01, -0.56] † | +4.12 [+3.49, +4.74] | +11.28 [+9.89, +12.57] |
| A4 · single-model · icon_global · precip · L5 | icon_global | 33,948 | -0.71 [-0.92, -0.48] † | +4.34 [+3.78, +4.95] | +11.82 [+10.60, +13.06] |
| A4 · single-model · icon_global · precip · L6 | icon_global | 33,804 | -0.70 [-0.94, -0.47] † | +4.50 [+3.89, +5.15] | +12.20 [+10.80, +13.53] |

## Suppressed cells (no value computed)

| Experiment | Comparison | Status | Cells |
| --- | --- | --- | --- |
| A1 | shared-data | insufficient sample | 250 |
| A1 | shared-data | not defined | 240 |
| A1 | single-model | insufficient sample | 280 |
| A2 | shared-data | insufficient sample | 750 |
| A2 | shared-data | not defined | 180 |
| A2 | single-model | insufficient sample | 660 |
| A3 | shared-data | insufficient sample | 650 |
| A3 | shared-data | not defined | 240 |
| A3 | single-model | insufficient sample | 600 |
| A4 | shared-data | insufficient sample | 525 |
| A4 | shared-data | not defined | 240 |
| A4 | single-model | insufficient sample | 500 |
