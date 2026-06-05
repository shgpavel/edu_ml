# Compiler-flag importance — gradient boosting analysis

- 342 random flag configurations, 48 varied flags, 93 benchmark binaries across 16 projects.
- **runtime**: GBM cross-validated R² = 0.841 (linear baseline 0.590); 27 benches used.
- **size**: GBM cross-validated R² = 0.996 (linear baseline 0.988); 93 benches used.

## Runtime — top flags by effect (% change when ON, significant first)

| flag | category | effect % | 95% CI | sig | perm.imp |
|------|----------|---------:|--------|:---:|---------:|
| `-flto` | flto | -15.55 | [-18.93, -11.60] | ✔ | 0.6706 |
| `-flto=full` | flto | -11.15 | [-15.08, -6.85] | ✔ | 0.5766 |
| `-flto=auto` | flto | -9.74 | [-14.10, -5.01] | ✔ | 0.5074 |
| `-fvirtual-function-elimination` | whole_prog | -9.14 | [-16.00, -1.53] | ✔ | -0.0025 |
| `-finline-hint-functions` | inline | +8.76 | [+7.28, +10.28] | ✔ | 0.1609 |
| `-O1` | O | +8.22 | [+6.44, +10.00] | ✔ | 0.5457 |
| `-fwhole-program-vtables` | whole_prog | -6.76 | [-12.94, -0.37] | ✔ | 0.0003 |
| `-Os` | O | -6.02 | [-8.89, -3.09] | ✔ | 0.0078 |
| `-fno-strict-aliasing` | strict | +3.94 | [-0.26, +7.20] |  | 0.0010 |
| `-fapprox-func` | fast_math | -3.77 | [-9.33, +1.56] |  | 0.0001 |
| `-fmerge-all-constants` | sections | +2.93 | [-0.07, +5.71] |  | -0.0003 |
| `-fstack-clash-protection` | stack_prot | -2.87 | [-6.99, +1.37] |  | -0.0009 |
| `-fno-delete-null-pointer-checks` | strict | -2.70 | [-9.63, +4.28] |  | 0.0032 |
| `-fno-omit-frame-pointer` | strict | -2.62 | [-7.83, +2.51] |  | -0.0001 |
| `-fstrict-aliasing` | strict | +2.39 | [-2.47, +6.69] |  | -0.0001 |
| `-O3` | O | -2.36 | [-5.34, +0.66] |  | 0.0010 |
| `-fstrict-enums` | strict | -2.29 | [-7.66, +2.83] |  | -0.0008 |
| `-flto=thin` | flto | -1.99 | [-3.33, -0.63] | ✔ | 0.0496 |
| `-march=native` | arch | +1.90 | [-1.00, +4.56] |  | 0.0012 |
| `-ffunction-sections` | sections | -1.82 | [-6.05, +2.33] |  | -0.0002 |

## Size — top flags by effect (% change when ON, significant first)

| flag | category | effect % | 95% CI | sig | perm.imp |
|------|----------|---------:|--------|:---:|---------:|
| `-flto` | flto | -34.62 | [-36.83, -32.17] | ✔ | 0.6940 |
| `-flto=full` | flto | -32.96 | [-35.41, -30.35] | ✔ | 0.7252 |
| `-flto=auto` | flto | -31.54 | [-34.20, -28.76] | ✔ | 0.6017 |
| `-fvirtual-function-elimination` | whole_prog | -30.92 | [-34.45, -27.20] | ✔ | 0.0001 |
| `-fwhole-program-vtables` | whole_prog | -27.08 | [-31.15, -22.82] | ✔ | 0.0001 |
| `-flto=thin` | flto | -22.07 | [-24.69, -19.34] | ✔ | 0.2891 |
| `-Os` | O | -18.76 | [-24.15, -13.18] | ✔ | 0.0467 |
| `-fno-delete-null-pointer-checks` | strict | -12.29 | [-24.78, +2.26] |  | 0.0000 |
| `-O2` | O | +11.74 | [+4.79, +19.03] | ✔ | 0.0002 |
| `-fmerge-all-constants` | sections | +9.75 | [+2.46, +17.55] | ✔ | 0.0000 |
| `-mprefer-vector-width=none` | vec_width | -7.08 | [-14.34, +0.69] |  | 0.0000 |
| `-mprefer-vector-width=256` | vec_width | +6.59 | [-2.82, +16.16] |  | -0.0000 |
| `-ffunction-sections` | sections | -6.51 | [-15.24, +2.55] |  | -0.0000 |
| `-O3` | O | +6.31 | [-1.08, +14.33] |  | 0.0012 |
| `-fno-vectorize` | vectorize | -6.15 | [-13.19, +1.36] |  | 0.0002 |
| `-funsafe-math-optimizations` | fast_math | -5.85 | [-16.87, +5.64] |  | -0.0000 |
| `-fstack-protector` | stack_prot | +5.42 | [-4.08, +15.04] |  | 0.0000 |
| `-fno-omit-frame-pointer` | strict | -5.25 | [-16.64, +7.78] |  | 0.0001 |
| `-fstack-clash-protection` | stack_prot | -4.65 | [-13.69, +5.17] |  | -0.0000 |
| `-finline-hint-functions` | inline | +4.64 | [-4.75, +14.50] |  | 0.0011 |
