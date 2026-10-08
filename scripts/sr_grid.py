# Rejilla del método S/R de John (setup sr_bounce). Uso: PYTHONPATH=. python scripts/sr_grid.py configs/nas100.toml 1min
import sys, itertools, numpy as np, pandas as pd
from botscalping.experiment import load_config
from botscalping.data import load_mt5_csv, split_by_date
from botscalping import components as comps, stats
from botscalping.engine import StrategySpec, build_signals, run_backtest, Costs, Exits
cfg = load_config(sys.argv[1]); tf = sys.argv[2]
b, _ = split_by_date(load_mt5_csv(cfg.data_path, cfg.spec.point, cfg.broker_tz), cfg.in_sample_until)
z = b.assign(spread=0.0)
mb = {"1min": 120, "5min": 390, "15min": 720, "60min": 1440}[tf]
EXITS = {"1:1": Exits(1, mb), "1:2": Exits(2, mb), "trailing 1ATR": Exits(0, mb, trail_atr=1.0),
         "BE 1R + trailing 2ATR": Exits(0, mb, breakeven_r=1.0, trail_atr=2.0, trail_start_r=1.0),
         "cierre al cruzar EMA20": Exits(0, mb, exit_ema=20)}
ctxs = {"neto": comps.Context(b, cfg.spec), "bruto": comps.Context(z, cfg.spec)}
years = sorted(set(b.index.year) - {b.index.year.min()})
rows = []
for k, wick in itertools.product([3, 5, 10], [0.0, 0.4]):
    for ename, ex in EXITS.items():
        strat = StrategySpec("sr_bounce", {"tf": tf, "k": k, "wick": wick}, [], ex)
        row = {"tf": tf, "k": k, "mecha": wick, "salida": ename}
        for lab, data, costs in [("bruto", z, Costs()), ("neto", b, cfg.costs)]:
            lo, sh, st, _ = build_signals(ctxs[lab], strat)
            t = run_backtest(data, lo, sh, st, ex, costs)
            r = t["r"].to_numpy()
            row[f"exp_{lab}"] = r.mean()
            if lab == "neto":
                bs = stats.bootstrap_mean(r, n_boot=1000)
                by = t.groupby(t["entry_time"].dt.year)["r"].mean().reindex(years)
                pts = (t["exit"] - t["entry"]) * t["side"]
                row.update(n=len(r), win=(r > 0).mean(), ci_lo=bs["ci_low"], ci_hi=bs["ci_high"], p=bs["p_gt_0"],
                           años_pos=int((by > 0).sum()), stop_med=t["risk"].median(), pts_medio=pts.mean(), dur_med=t["bars"].median())
        rows.append(row)
        print(row, flush=True, file=sys.stderr)
df = pd.DataFrame(rows)
df.to_csv(f"results/sr_{cfg.spec.symbol}_{tf}.csv", index=False)
