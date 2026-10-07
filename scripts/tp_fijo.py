# Rebote en nivel (M5) con objetivo fijo pequeño "unos pips". Uso: PYTHONPATH=. python scripts/tp_fijo.py configs/nas100.toml 10,15,20,30,40
import sys, numpy as np, pandas as pd
from botscalping.experiment import load_config
from botscalping.data import load_mt5_csv, split_by_date
from botscalping.indicators import resample_ohlc
from botscalping import components as comps, stats
from botscalping.engine import StrategySpec, build_signals, run_backtest, Costs, Exits
cfg = load_config(sys.argv[1]); tps = [float(x) for x in sys.argv[2].split(",")]
b, _ = split_by_date(load_mt5_csv(cfg.data_path, cfg.spec.point, cfg.broker_tz), cfg.in_sample_until)
b = resample_ohlc(b, "5min")
rows = []
for lbm in [120, 480]:
    lb = lbm // 5
    for tp in tps:
        ex = Exits(1.0, 48, tp_price=tp)
        strat = StrategySpec("level_bounce", {"lookback": lb, "gap": max(3, lb // 8), "wick": 0.4}, [], ex)
        row = {"horas_nivel": lbm / 60, "tp": tp}
        for lab, data, costs in [("bruto", b.assign(spread=0.0), Costs()), ("neto", b, cfg.costs)]:
            lo, sh, st, _ = build_signals(comps.Context(data, cfg.spec), strat)
            t = run_backtest(data, lo, sh, st, ex, costs)
            pts = ((t["exit"] - t["entry"]) * t["side"]).to_numpy()
            row[f"pts_{lab}"] = pts.mean()
            if lab == "neto":
                bs = stats.bootstrap_mean(pts, n_boot=1000)
                row.update(n=len(t), acierto=(pts > 0).mean(), ci_lo=bs["ci_low"], ci_hi=bs["ci_high"],
                           stop_med=t["risk"].median(), total_pts=pts.sum())
        rows.append(row)
pd.set_option("display.width", 250)
print(cfg.spec.symbol, "(resultado por operación en PUNTOS de precio)")
print(pd.DataFrame(rows).round(3).to_string(index=False))
