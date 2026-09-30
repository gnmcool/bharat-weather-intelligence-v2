# M4.4-C — model agreement (VM-1.1, census m4.4-a-census-2@55030a4)

**Weather-model rainfall-event agreement only (ECMWF, GFS, ICON).** Not CORE risk verification and not a calibrated forecast statement.

Each cell reads: "In the archived sample … when k of 3 models forecast ≥ τ, the reference reached ≥ τ on x of n days." The k-groups of one lead and threshold partition the same sample. They are mutually exclusive, not independent samples, and their intervals must not be compared as if they were independent.

◊ = Degenerate bootstrap interval: all bootstrap replicates produced the same boundary value; this does not imply statistical certainty.

Code 7883abb; archive-index 24534f6. IMD (C3) and ERA5 (C4) are separate; their counts are never combined. Lead 7 is not analysed (ICON not defined).

## Primary — IMD, pooled, all seasons, leads 1–4

| Lead | Threshold (mm) | k=0 | k=1 | k=2 | k=3 |
| --- | --- | --- | --- | --- | --- |
| 1 | 35.6 | 438 of 22,696 = 0.019 [0.015, 0.024] | 143 of 652 = 0.219 [0.186, 0.252] | 115 of 230 = 0.500 [0.442, 0.550] | insufficient sample (n 86) |
| 1 | 64.5 | 197 of 23,376 = 0.008 [0.006, 0.011] | 45 of 234 = 0.192 [0.133, 0.256] | insufficient sample (n 42) | insufficient sample (n 12) |
| 1 | 115.6 | 60 of 23,610 = 0.003 [0.002, 0.004] | insufficient sample (n 50) | insufficient sample (n 3) | insufficient sample (n 1) |
| 2 | 35.6 | 443 of 22,633 = 0.020 [0.015, 0.024] | 163 of 701 = 0.233 [0.195, 0.266] | 110 of 232 = 0.474 [0.420, 0.526] | insufficient sample (n 64) |
| 2 | 64.5 | 202 of 23,358 = 0.009 [0.006, 0.011] | 46 of 221 = 0.208 [0.153, 0.268] | insufficient sample (n 45) | insufficient sample (n 6) |
| 2 | 115.6 | 60 of 23,586 = 0.003 [0.002, 0.004] | insufficient sample (n 42) | insufficient sample (n 2) | insufficient sample (n 0) |
| 3 | 35.6 | 456 of 22,505 = 0.020 [0.016, 0.025] | 167 of 830 = 0.201 [0.174, 0.232] | 103 of 206 = 0.500 [0.419, 0.582] | insufficient sample (n 55) |
| 3 | 64.5 | 207 of 23,292 = 0.009 [0.006, 0.011] | 46 of 267 = 0.172 [0.125, 0.211] | insufficient sample (n 32) | insufficient sample (n 5) |
| 3 | 115.6 | 64 of 23,546 = 0.003 [0.002, 0.004] | insufficient sample (n 50) | insufficient sample (n 0) | insufficient sample (n 0) |
| 4 | 35.6 | 493 of 22,536 = 0.022 [0.017, 0.027] | 153 of 795 = 0.192 [0.166, 0.217] | 90 of 193 = 0.466 [0.372, 0.547] | insufficient sample (n 38) |
| 4 | 64.5 | 221 of 23,281 = 0.009 [0.007, 0.012] | 31 of 243 = 0.128 [0.086, 0.176] | insufficient sample (n 34) | insufficient sample (n 4) |
| 4 | 115.6 | 67 of 23,502 = 0.003 [0.002, 0.004] | insufficient sample (n 59) | insufficient sample (n 1) | insufficient sample (n 0) |

## Secondary — ERA5, pooled, all seasons, leads 1–4

| Lead | Threshold (mm) | k=0 | k=1 | k=2 | k=3 |
| --- | --- | --- | --- | --- | --- |
| 1 | 35.6 | 351 of 32,298 = 0.011 [0.009, 0.013] | 210 of 939 = 0.224 [0.195, 0.252] | 151 of 292 = 0.517 [0.457, 0.574] | 108 of 131 = 0.824 [0.752, 0.882] |
| 1 | 64.5 | 136 of 33,288 = 0.004 [0.003, 0.005] | 60 of 297 = 0.202 [0.155, 0.247] | insufficient sample (n 56) | insufficient sample (n 19) |
| 1 | 115.6 | 33 of 33,579 = 0.001 [0.001, 0.002] | insufficient sample (n 75) | insufficient sample (n 6) | insufficient sample (n 0) |
| 2 | 35.6 | 389 of 32,265 = 0.012 [0.010, 0.015] | 202 of 964 = 0.210 [0.177, 0.239] | 163 of 310 = 0.526 [0.477, 0.584] | insufficient sample (n 85) |
| 2 | 64.5 | 143 of 33,242 = 0.004 [0.003, 0.006] | 59 of 310 = 0.190 [0.147, 0.238] | insufficient sample (n 58) | insufficient sample (n 14) |
| 2 | 115.6 | 32 of 33,554 = 0.001 [0.001, 0.001] | insufficient sample (n 65) | insufficient sample (n 3) | insufficient sample (n 2) |
| 3 | 35.6 | 422 of 32,279 = 0.013 [0.011, 0.016] | 238 of 1,119 = 0.213 [0.184, 0.239] | 110 of 264 = 0.417 [0.360, 0.471] | insufficient sample (n 70) |
| 3 | 64.5 | 153 of 33,327 = 0.005 [0.003, 0.006] | 60 of 349 = 0.172 [0.133, 0.215] | insufficient sample (n 47) | insufficient sample (n 9) |
| 3 | 115.6 | 33 of 33,663 = 0.001 [0.001, 0.001] | insufficient sample (n 62) | insufficient sample (n 5) | insufficient sample (n 2) |
| 4 | 35.6 | 469 of 32,271 = 0.015 [0.011, 0.018] | 206 of 1,111 = 0.185 [0.160, 0.211] | 104 of 258 = 0.403 [0.346, 0.458] | insufficient sample (n 56) |
| 4 | 64.5 | 175 of 33,321 = 0.005 [0.004, 0.007] | 43 of 326 = 0.132 [0.089, 0.178] | insufficient sample (n 43) | insufficient sample (n 6) |
| 4 | 115.6 | 34 of 33,613 = 0.001 [0.001, 0.001] | insufficient sample (n 78) | insufficient sample (n 4) | insufficient sample (n 1) |

## Exploratory — leads 5–6

**Limitation:** GFS rainfall source representation changes at this lead range. The effect on the verification metric and on the model-agreement distribution is unresolved. A lower GFS event count at these leads does not mean improved or degraded forecast skill.

### C3 (IMD)

| Lead | Threshold (mm) | k=0 | k=1 | k=2 | k=3 |
| --- | --- | --- | --- | --- | --- |
| 5 | 35.6 | 536 of 22,707 = 0.024 [0.018, 0.029] | 170 of 707 = 0.240 [0.200, 0.279] | 52 of 105 = 0.495 [0.385, 0.605] | insufficient sample (n 9) |
| 5 | 64.5 | 232 of 23,313 = 0.010 [0.008, 0.013] | 30 of 200 = 0.150 [0.094, 0.217] | insufficient sample (n 15) | insufficient sample (n 0) |
| 5 | 115.6 | 65 of 23,483 = 0.003 [0.002, 0.004] | insufficient sample (n 43) | insufficient sample (n 2) | insufficient sample (n 0) |
| 6 | 35.6 | 556 of 22,701 = 0.024 [0.019, 0.031] | 161 of 676 = 0.238 [0.197, 0.279] | 44 of 114 = 0.386 [0.295, 0.467] | insufficient sample (n 3) |
| 6 | 64.5 | 235 of 23,290 = 0.010 [0.007, 0.013] | 28 of 190 = 0.147 [0.100, 0.201] | insufficient sample (n 13) | insufficient sample (n 1) |
| 6 | 115.6 | 68 of 23,455 = 0.003 [0.002, 0.004] | insufficient sample (n 36) | insufficient sample (n 3) | insufficient sample (n 0) |

### C4 (ERA5)

| Lead | Threshold (mm) | k=0 | k=1 | k=2 | k=3 |
| --- | --- | --- | --- | --- | --- |
| 5 | 35.6 | 522 of 32,297 = 0.016 [0.013, 0.020] | 226 of 958 = 0.236 [0.208, 0.266] | 61 of 140 = 0.436 [0.352, 0.519] | insufficient sample (n 13) |
| 5 | 64.5 | 190 of 33,115 = 0.006 [0.004, 0.007] | 35 of 265 = 0.132 [0.098, 0.170] | insufficient sample (n 26) | insufficient sample (n 2) |
| 5 | 115.6 | 38 of 33,348 = 0.001 [0.001, 0.002] | insufficient sample (n 56) | insufficient sample (n 4) | insufficient sample (n 0) |
| 6 | 35.6 | 563 of 32,385 = 0.017 [0.014, 0.021] | 192 of 945 = 0.203 [0.174, 0.231] | 61 of 145 = 0.421 [0.333, 0.500] | insufficient sample (n 5) |
| 6 | 64.5 | 187 of 33,195 = 0.006 [0.004, 0.007] | 39 of 265 = 0.147 [0.102, 0.193] | insufficient sample (n 19) | insufficient sample (n 1) |
| 6 | 115.6 | 40 of 33,424 = 0.001 [0.001, 0.002] | insufficient sample (n 54) | insufficient sample (n 1) | insufficient sample (n 1) |

## Exploratory — which models make up k = 1 and k = 2 (IMD, leads 1–4)

| Lead | Threshold (mm) | ECMWF | GFS | ICON | ECMWF+GFS | ECMWF+ICON | GFS+ICON |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 35.6 | 42 of 221 = 0.190 [0.125, 0.249] | 58 of 211 = 0.275 [0.218, 0.333] | 43 of 220 = 0.195 [0.138, 0.251] | insufficient sample (n 86) | 44 of 100 = 0.440 [0.333, 0.537] | insufficient sample (n 44) |
| 1 | 64.5 | insufficient sample (n 71) | insufficient sample (n 81) | insufficient sample (n 82) | insufficient sample (n 17) | insufficient sample (n 14) | insufficient sample (n 11) |
| 1 | 115.6 | insufficient sample (n 13) | insufficient sample (n 19) | insufficient sample (n 18) | insufficient sample (n 1) | insufficient sample (n 1) | insufficient sample (n 1) |
| 2 | 35.6 | 56 of 240 = 0.233 [0.176, 0.283] | 66 of 246 = 0.268 [0.211, 0.329] | 41 of 215 = 0.191 [0.129, 0.252] | insufficient sample (n 86) | 48 of 105 = 0.457 [0.366, 0.537] | insufficient sample (n 41) |
| 2 | 64.5 | insufficient sample (n 69) | insufficient sample (n 81) | insufficient sample (n 71) | insufficient sample (n 14) | insufficient sample (n 26) | insufficient sample (n 5) |
| 2 | 115.6 | insufficient sample (n 11) | insufficient sample (n 17) | insufficient sample (n 14) | insufficient sample (n 1) | insufficient sample (n 0) | insufficient sample (n 1) |
| 3 | 35.6 | 61 of 298 = 0.205 [0.164, 0.248] | 49 of 288 = 0.170 [0.126, 0.214] | 57 of 244 = 0.234 [0.182, 0.283] | insufficient sample (n 82) | insufficient sample (n 82) | insufficient sample (n 42) |
| 3 | 64.5 | insufficient sample (n 77) | 17 of 102 = 0.167 [0.093, 0.269] | insufficient sample (n 88) | insufficient sample (n 12) | insufficient sample (n 15) | insufficient sample (n 5) |
| 3 | 115.6 | insufficient sample (n 14) | insufficient sample (n 19) | insufficient sample (n 17) | insufficient sample (n 0) | insufficient sample (n 0) | insufficient sample (n 0) |
| 4 | 35.6 | 46 of 275 = 0.167 [0.129, 0.211] | 61 of 301 = 0.203 [0.159, 0.237] | 46 of 219 = 0.210 [0.152, 0.271] | insufficient sample (n 89) | insufficient sample (n 74) | insufficient sample (n 30) |
| 4 | 64.5 | insufficient sample (n 76) | insufficient sample (n 94) | insufficient sample (n 73) | insufficient sample (n 14) | insufficient sample (n 15) | insufficient sample (n 5) |
| 4 | 115.6 | insufficient sample (n 13) | insufficient sample (n 30) | insufficient sample (n 16) | insufficient sample (n 0) | insufficient sample (n 1) | insufficient sample (n 0) |

ERA5, leads 5–6 and every other cell: `agreement_results.csv`.

