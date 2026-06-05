#!/usr/bin/env python3
"""
Gradient-boosting analysis of which clang optimization flags actually matter
for (a) runtime and (b) binary size, across the collected benchmark dataset.

Data: clang-ml/lrndata/*.json  -- each record is one random flag configuration
tested on 16 projects (~93 benchmark binaries), measuring `seconds` and `bytes`.

Because flags were sampled randomly and independently per category, the dataset
is effectively a randomized experiment: model-free "flag on vs off" contrasts
estimate causal main effects, and the gradient-boosted model captures any
interactions on top.

Outputs:
  analysis/plots/*.png   -- figures
  analysis/flag_effects.csv, flag_effects.md -- the numbers behind the plots
"""

import os
import re
import json
import glob
import importlib.util
import warnings

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from xgboost import XGBRegressor
from sklearn.model_selection import KFold
from sklearn.inspection import permutation_importance
from sklearn.linear_model import RidgeCV
from sklearn.metrics import r2_score

warnings.filterwarnings("ignore")
RNG = np.random.default_rng(0)
SEED = 0

HERE = os.path.abspath(os.path.dirname(__file__))
OUTDIR = os.path.join(HERE, "analysis")
PLOTDIR = os.path.join(OUTDIR, "plots")
os.makedirs(PLOTDIR, exist_ok=True)

RUNTIME_MIN_SECONDS = 0.05  # ignore sub-50ms benches: overhead-dominated, pure noise

# ----------------------------------------------------------------------------
# 1. Load data + flag vocabulary
# ----------------------------------------------------------------------------
def load_flag_vocab():
    spec = importlib.util.spec_from_file_location("gd", os.path.join(HERE, "get-data.py"))
    gd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gd)
    return gd.FLAG_VARIANTS  # {category: [flag, ...]}


def load_dataset():
    data = []
    for fn in sorted(glob.glob(os.path.join(HERE, "lrndata", "*.json"))):
        data += json.load(open(fn))
    # all flag strings are unique across files (verified), so just concatenate
    return data


FLAG_VARIANTS = load_flag_vocab()
FLAG2CAT = {f: c for c, fs in FLAG_VARIANTS.items() for f in fs}
ALL_FLAGS = [f for fs in FLAG_VARIANTS.values() for f in fs]
data = load_dataset()
print(f"Loaded {len(data)} flag configurations")

# ----------------------------------------------------------------------------
# 2. Build feature matrix (one binary column per individual flag) and the
#    per-(config, bench) long table of measurements.
# ----------------------------------------------------------------------------
feat_rows = []
long_rows = []
for ci, entry in enumerate(data):
    flags = set(entry["flags"].split())
    feat_rows.append({f: int(f in flags) for f in ALL_FLAGS})
    for proj, blist in entry["results"].items():
        for b in blist:
            long_rows.append(
                dict(config=ci, project=proj, bench=f"{proj}/{b['bench']}",
                     seconds=b["seconds"], bytes=b["bytes"])
            )

X = pd.DataFrame(feat_rows)
X = X.loc[:, X.sum() > 0]                       # drop flags never used (Ofast, etc.)
FLAGS = list(X.columns)
print(f"Usable flags (non-constant): {len(FLAGS)}")

long = pd.DataFrame(long_rows)

# ----------------------------------------------------------------------------
# 3. Targets: per-benchmark log-normalised, then averaged per config.
#    target[c] = mean_b ( log m[c,b] - mean_c log m[c,b] )  = log geomean ratio.
#    Negative => faster / smaller than the typical config.
# ----------------------------------------------------------------------------
def per_config_score(df, value_col, bench_keep=None):
    d = df if bench_keep is None else df[df.bench.isin(bench_keep)]
    d = d.assign(logv=np.log(d[value_col]))
    d["rel"] = d.logv - d.groupby("bench")["logv"].transform("mean")
    return d.groupby("config")["rel"].mean()


bench_med = long.groupby("bench")["seconds"].median()
runtime_benches = sorted(bench_med[bench_med >= RUNTIME_MIN_SECONDS].index)
print(f"Runtime benches >= {RUNTIME_MIN_SECONDS}s: {len(runtime_benches)} "
      f"(of {long.bench.nunique()}); size uses all binaries")

y_rt = per_config_score(long, "seconds", runtime_benches).reindex(X.index).values
y_sz = per_config_score(long, "bytes").reindex(X.index).values

TARGETS = {
    "runtime": dict(y=y_rt, unit="runtime", nbench=len(runtime_benches)),
    "size":    dict(y=y_sz, unit="binary size", nbench=long.bench.nunique()),
}

# ----------------------------------------------------------------------------
# 4. Gradient boosting model + honest cross-validated evaluation & importances
# ----------------------------------------------------------------------------
def make_model():
    return XGBRegressor(
        n_estimators=400, learning_rate=0.03, max_depth=3,
        subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0,
        min_child_weight=3, random_state=SEED, n_jobs=4,
    )


def evaluate(Xdf, y):
    """5-fold CV: out-of-fold predictions, R^2, and held-out permutation importance."""
    Xv = Xdf.values
    kf = KFold(n_splits=5, shuffle=True, random_state=SEED)
    oof = np.full(len(y), np.nan)
    perm = np.zeros((5, Xv.shape[1]))
    lin_oof = np.full(len(y), np.nan)
    for k, (tr, te) in enumerate(kf.split(Xv)):
        m = make_model().fit(Xv[tr], y[tr])
        oof[te] = m.predict(Xv[te])
        pi = permutation_importance(m, Xv[te], y[te], scoring="r2",
                                    n_repeats=30, random_state=SEED)
        perm[k] = pi.importances_mean
        lin = RidgeCV(alphas=np.logspace(-2, 3, 20)).fit(Xv[tr], y[tr])
        lin_oof[te] = lin.predict(Xv[te])
    return dict(
        oof=oof, r2=r2_score(y, oof), lin_r2=r2_score(y, lin_oof),
        perm=pd.Series(perm.mean(0), index=Xdf.columns),
    )


def shap_and_gain(Xdf, y):
    """Full-data model -> TreeSHAP contributions (direction) + gain importance."""
    m = make_model().fit(Xdf.values, y)
    booster = m.get_booster()
    import xgboost as xgb
    contribs = booster.predict(xgb.DMatrix(Xdf.values), pred_contribs=True)
    shap = pd.DataFrame(contribs[:, :-1], columns=Xdf.columns)  # last col = bias
    gain = pd.Series(
        {f: m.get_booster().get_score(importance_type="gain").get(fc, 0.0)
         for f, fc in zip(Xdf.columns, [f"f{i}" for i in range(Xdf.shape[1])])},
    )
    return shap, gain, m


def marginal_effects(Xdf, y, n_boot=4000):
    """Model-free: mean(y|flag on) - mean(y|flag off), bootstrap 95% CI. Log units."""
    Xv = Xdf.values
    n = len(y)
    out = {}
    boot_idx = RNG.integers(0, n, size=(n_boot, n))
    for j, f in enumerate(Xdf.columns):
        on = Xv[:, j] == 1
        d = y[on].mean() - y[~on].mean()
        bs = np.empty(n_boot)
        col = Xv[:, j]
        for b in range(n_boot):
            idx = boot_idx[b]
            yi, ci = y[idx], col[idx]
            m1 = ci == 1
            if m1.any() and (~m1).any():
                bs[b] = yi[m1].mean() - yi[~m1].mean()
            else:
                bs[b] = np.nan
        lo, hi = np.nanpercentile(bs, [2.5, 97.5])
        out[f] = dict(delta=d, lo=lo, hi=hi, n_on=int(on.sum()))
    return pd.DataFrame(out).T


print("\nFitting models...")
RESULTS = {}
for name, t in TARGETS.items():
    y = t["y"]
    ev = evaluate(X, y)
    shap, gain, model = shap_and_gain(X, y)
    me = marginal_effects(X, y)
    RESULTS[name] = dict(ev=ev, shap=shap, gain=gain, model=model, me=me, y=y)
    print(f"  {name:8s}: GBM CV R^2 = {ev['r2']:+.3f}   "
          f"(linear baseline R^2 = {ev['lin_r2']:+.3f})   benches={t['nbench']}")

# convert log effect -> percent
pct = lambda x: (np.exp(x) - 1.0) * 100.0

# ----------------------------------------------------------------------------
# 5. Plotting helpers
# ----------------------------------------------------------------------------
plt.rcParams.update({
    "figure.dpi": 130, "savefig.dpi": 150, "font.size": 10,
    "axes.grid": True, "grid.alpha": 0.25, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False,
})
GOOD, BAD, NEU = "#2a9d4a", "#c0392b", "#3a6ea5"   # green good / red bad / blue


def save(fig, fn):
    fig.tight_layout()
    p = os.path.join(PLOTDIR, fn)
    fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    print("  wrote", os.path.relpath(p, HERE))


def fig_importance(name, topn=18):
    perm = RESULTS[name]["ev"]["perm"].sort_values(ascending=False).head(topn)[::-1]
    fig, ax = plt.subplots(figsize=(8, 0.42 * len(perm) + 1.2))
    ax.barh(range(len(perm)), perm.values, color=NEU)
    ax.set_yticks(range(len(perm)))
    ax.set_yticklabels(perm.index, fontsize=9)
    ax.set_xlabel("Permutation importance (drop in CV $R^2$ when flag is shuffled)")
    ax.set_title(f"Which flags drive {TARGETS[name]['unit']}?  "
                 f"(gradient boosting, held-out)\nGBM CV $R^2$={RESULTS[name]['ev']['r2']:.2f}",
                 fontsize=11, loc="left")
    save(fig, f"fig_{name}_importance.png")


def fig_effects(name, topn=18):
    me = RESULTS[name]["me"].copy()
    me["abs"] = me["delta"].abs()
    me = me.sort_values("abs", ascending=False).head(topn)
    me = me.sort_values("delta")  # most-negative (good) at bottom
    d, lo, hi = pct(me["delta"].values), pct(me["lo"].values), pct(me["hi"].values)
    sig = (me["lo"] > 0) | (me["hi"] < 0)
    colors = [BAD if v > 0 else GOOD for v in d]
    colors = [c if s else "#b0b0b0" for c, s in zip(colors, sig)]
    fig, ax = plt.subplots(figsize=(8.4, 0.44 * len(me) + 1.4))
    ax.barh(range(len(me)), d, color=colors,
            xerr=[d - lo, hi - d], error_kw=dict(ecolor="#444", lw=1, capsize=2.5))
    ax.axvline(0, color="k", lw=0.8)
    ax.set_yticks(range(len(me)))
    ax.set_yticklabels(me.index, fontsize=9)
    ax.set_xlabel(f"% change in {TARGETS[name]['unit']} when flag is ON  "
                  f"(← better / worse →)")
    ax.set_title(f"Effect of each flag on {TARGETS[name]['unit']} "
                 f"(flag on vs off, 95% bootstrap CI)", fontsize=11, loc="left")
    legend = [Line2D([0], [0], color=GOOD, lw=8, label="improves (significant)"),
              Line2D([0], [0], color=BAD, lw=8, label="worsens (significant)"),
              Line2D([0], [0], color="#b0b0b0", lw=8, label="CI includes 0")]
    ax.legend(handles=legend, fontsize=8, loc="lower right", framealpha=0.9)
    save(fig, f"fig_{name}_effects.png")


def fig_opt_levels():
    olevels = [f for f in ["-O1", "-O2", "-O3", "-Os"] if f in FLAGS]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, name in zip(axes, ["runtime", "size"]):
        y = RESULTS[name]["y"]
        means, los, his = [], [], []
        for f in olevels:
            grp = y[X[f].values == 1]
            bs = [RNG.choice(grp, len(grp)).mean() for _ in range(3000)]
            means.append(pct(grp.mean()))
            lo, hi = np.percentile(bs, [2.5, 97.5])
            los.append(pct(lo)); his.append(pct(hi))
        means = np.array(means)
        cols = [GOOD if m < 0 else BAD for m in means]
        ax.bar(range(len(olevels)), means, color=cols,
               yerr=[means - np.array(los), np.array(his) - means],
               error_kw=dict(ecolor="#333", lw=1.2, capsize=4))
        ax.axhline(0, color="k", lw=0.8)
        ax.set_xticks(range(len(olevels))); ax.set_xticklabels(olevels)
        ax.set_title(f"{TARGETS[name]['unit'].title()} by -O level", fontsize=11)
        ax.set_ylabel(f"% vs dataset average ({TARGETS[name]['unit']})")
    fig.suptitle("Optimization level: the dominant knob "
                 "(mean of each group vs overall average)", fontsize=12)
    save(fig, "fig_opt_levels.png")


def fig_category_importance():
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    for ax, name in zip(axes, ["runtime", "size"]):
        perm = RESULTS[name]["ev"]["perm"].clip(lower=0)
        cat = perm.groupby(FLAG2CAT).sum().sort_values()
        ax.barh(range(len(cat)), cat.values, color=NEU)
        ax.set_yticks(range(len(cat))); ax.set_yticklabels(cat.index, fontsize=9)
        ax.set_xlabel("summed permutation importance")
        ax.set_title(TARGETS[name]["unit"].title(), fontsize=11)
    fig.suptitle("Flag-category importance (individual flags grouped by knob)",
                 fontsize=12)
    save(fig, "fig_category_importance.png")


def fig_model_quality():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    for ax, name in zip(axes, ["runtime", "size"]):
        ev = RESULTS[name]["ev"]; y = RESULTS[name]["y"]
        ax.scatter(pct(y), pct(ev["oof"]), s=16, alpha=0.5, color=NEU,
                   edgecolor="none")
        lim = [pct(min(y.min(), ev["oof"].min())), pct(max(y.max(), ev["oof"].max()))]
        ax.plot(lim, lim, "k--", lw=1, alpha=0.6)
        ax.set_xlabel(f"actual % vs avg ({TARGETS[name]['unit']})")
        ax.set_ylabel("predicted (out-of-fold)")
        ax.set_title(f"{TARGETS[name]['unit'].title()}:  GBM $R^2$={ev['r2']:.2f}"
                     f"   vs linear $R^2$={ev['lin_r2']:.2f}", fontsize=11)
    fig.suptitle("Model validity: cross-validated predicted vs actual",
                 fontsize=12)
    save(fig, "fig_model_quality.png")


def fig_shap_beeswarm(name, topn=14):
    shap = RESULTS[name]["shap"]
    order = shap.abs().mean().sort_values(ascending=False).head(topn).index[::-1]
    fig, ax = plt.subplots(figsize=(8.6, 0.46 * len(order) + 1.3))
    for i, f in enumerate(order):
        sv = pct_shap = (np.exp(shap[f].values) - 1) * 100
        xv = X[f].values
        jit = (RNG.random(len(sv)) - 0.5) * 0.7
        for val, col, lab in [(1, BAD, None), (0, NEU, None)]:
            m = xv == val
            ax.scatter(sv[m], i + jit[m], s=10, alpha=0.5, color=col,
                       edgecolor="none")
    ax.axvline(0, color="k", lw=0.8)
    ax.set_yticks(range(len(order))); ax.set_yticklabels(order, fontsize=9)
    ax.set_xlabel(f"SHAP contribution to {TARGETS[name]['unit']} "
                  f"(% vs avg; ← better / worse →)")
    ax.set_title(f"How each flag pushes {TARGETS[name]['unit']} per config "
                 f"(TreeSHAP)", fontsize=11, loc="left")
    leg = [Line2D([0], [0], marker="o", color="w", markerfacecolor=BAD,
                  markersize=8, label="flag ON"),
           Line2D([0], [0], marker="o", color="w", markerfacecolor=NEU,
                  markersize=8, label="flag OFF")]
    ax.legend(handles=leg, fontsize=8, loc="lower right")
    save(fig, f"fig_{name}_shap.png")


# ----------------------------------------------------------------------------
# 6. Generate everything
# ----------------------------------------------------------------------------
print("\nWriting figures...")
for name in ["runtime", "size"]:
    fig_importance(name)
    fig_effects(name)
    fig_shap_beeswarm(name)
fig_opt_levels()
fig_category_importance()
fig_model_quality()

# ----------------------------------------------------------------------------
# 7. Dump the numbers
# ----------------------------------------------------------------------------
tables = []
for name in ["runtime", "size"]:
    me = RESULTS[name]["me"]; perm = RESULTS[name]["ev"]["perm"]
    t = pd.DataFrame({
        "flag": me.index,
        "category": [FLAG2CAT.get(f, "?") for f in me.index],
        "target": name,
        "n_configs_on": me["n_on"].astype(int).values,
        "perm_importance": perm.reindex(me.index).values,
        "effect_pct": pct(me["delta"].values),
        "ci_lo_pct": pct(me["lo"].values),
        "ci_hi_pct": pct(me["hi"].values),
    })
    t["significant"] = (t.ci_lo_pct > 0) | (t.ci_hi_pct < 0)
    tables.append(t)

tab = pd.concat(tables, ignore_index=True)
tab.to_csv(os.path.join(OUTDIR, "flag_effects.csv"), index=False)

with open(os.path.join(OUTDIR, "flag_effects.md"), "w") as f:
    f.write("# Compiler-flag importance — gradient boosting analysis\n\n")
    f.write(f"- {len(data)} random flag configurations, {len(FLAGS)} varied flags, "
            f"{long.bench.nunique()} benchmark binaries across 16 projects.\n")
    for name in ["runtime", "size"]:
        ev = RESULTS[name]["ev"]
        f.write(f"- **{name}**: GBM cross-validated R² = {ev['r2']:.3f} "
                f"(linear baseline {ev['lin_r2']:.3f}); "
                f"{TARGETS[name]['nbench']} benches used.\n")
    for name in ["runtime", "size"]:
        f.write(f"\n## {name.title()} — top flags by effect "
                f"(% change when ON, significant first)\n\n")
        t = tables[0 if name == "runtime" else 1].copy()
        t = t.reindex(t.effect_pct.abs().sort_values(ascending=False).index)
        f.write("| flag | category | effect % | 95% CI | sig | perm.imp |\n")
        f.write("|------|----------|---------:|--------|:---:|---------:|\n")
        for _, r in t.head(20).iterrows():
            f.write(f"| `{r.flag}` | {r.category} | {r.effect_pct:+.2f} | "
                    f"[{r.ci_lo_pct:+.2f}, {r.ci_hi_pct:+.2f}] | "
                    f"{'✔' if r.significant else ''} | {r.perm_importance:.4f} |\n")

print("\nWrote analysis/flag_effects.csv and analysis/flag_effects.md")
print("\n=== TOP SIGNIFICANT EFFECTS ===")
for name in ["runtime", "size"]:
    t = (tables[0 if name == "runtime" else 1]
         .query("significant").reindex(
             columns=["flag", "effect_pct", "ci_lo_pct", "ci_hi_pct"]))
    t = t.reindex(t.effect_pct.abs().sort_values(ascending=False).index)
    print(f"\n{name.upper()}  (negative % = better):")
    for _, r in t.head(12).iterrows():
        print(f"  {r.flag:34s} {r.effect_pct:+6.2f}%  "
              f"[{r.ci_lo_pct:+6.2f}, {r.ci_hi_pct:+6.2f}]")
