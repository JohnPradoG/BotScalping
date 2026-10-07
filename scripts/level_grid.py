# Rebote en niveles de horas antes (setup level_bounce). Uso: PYTHONPATH=. python scripts/level_grid.py configs/nas100.toml [5min]
import sys, itertools, numpy as np, pandas as pd
from botscalping.experiment import load_config
from botscalping.data import load_mt5_csv, split_by_date
from botscalping import components as comps, stats
from botscalping.engine import StrategySpec, build_signals, run_backtest, Costs, Exits
cfg = load_config(sys.argv[1])
from botscalping.indicators import resample_ohlc
b, _ = split_by_date(load_mt5_csv(cfg.data_path, cfg.spec.point, cfg.broker_tz), cfg.in_sample_until)
if len(sys.argv) > 2: b = resample_ohlc(b, sys.argv[2])  # opera todo en ese marco (p. ej. 5min)
z = b.assign(spread=0.0)
ctxs = {"neto": comps.Context(b, cfg.spec), "bruto": comps.Context(z, cfg.spec)}
years = sorted(set(b.index.year) - {b.index.year.min()})
rows = []
TF = int(pd.Timedelta(sys.argv[2]).total_seconds() // 60) if len(sys.argv) > 2 else 1
for lbm, wick, rr in itertools.product([60, 120, 240, 480], [0.0, 0.4], [1.0, 1.5, 2.0]):
    lb = lbm // TF; gap = max(3, lb // 8)
    ex = Exits(rr, 240 // TF)
    strat = StrategySpec("level_bounce", {"lookback": lb, "gap": gap, "wick": wick}, [], ex)
    row = {"horas": lbm / 60, "mecha": wick, "rr": rr}
    for lab, data, costs in [("bruto", z, Costs()), ("neto", b, cfg.costs)]:
        lo, sh, st, _ = build_signals(ctxs[lab], strat)
        t = run_backtest(data, lo, sh, st, ex, costs)
        r = t["r"].to_numpy()
        row[f"exp_{lab}"] = r.mean()
        if lab == "neto":
            bs = stats.bootstrap_mean(r, n_boot=1000)
            by = t.groupby(t["entry_time"].dt.year)["r"].mean().reindex(years)
            row.update(n=len(r), win=(r > 0).mean(), ci_lo=bs["ci_low"], ci_hi=bs["ci_high"], p=bs["p_gt_0"],
                       años_pos=int((by > 0).sum()), stop_med=t["risk"].median(),
                       coste_R=np.median((b["spread"].to_numpy()[t["signal_idx"].to_numpy() + 1] + 2 * cfg.costs.slippage) / t["risk"].to_numpy()))
    rows.append(row)
df = pd.DataFrame(rows)
df.to_csv(f"results/level_{cfg.spec.symbol}{"_" + sys.argv[2] if len(sys.argv) > 2 else ""}.csv", index=False)
pd.set_option("display.width", 250)
print(cfg.spec.symbol, "| netas > 0:", int((df.exp_neto > 0).sum()), "de", len(df))
print(df.sort_values("exp_neto", ascending=False).round(3).to_string(index=False))
