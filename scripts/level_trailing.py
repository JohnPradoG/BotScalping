# Rebote en nivel (M5) siguiendo el precio, sin objetivo fijo. Uso: PYTHONPATH=. python scripts/level_trailing.py configs/nas100.toml
import sys, itertools, numpy as np, pandas as pd
from botscalping.experiment import load_config
from botscalping.data import load_mt5_csv, split_by_date
from botscalping.indicators import resample_ohlc
from botscalping import components as comps, stats
from botscalping.engine import StrategySpec, build_signals, run_backtest, Costs, Exits
cfg = load_config(sys.argv[1])
b, _ = split_by_date(load_mt5_csv(cfg.data_path, cfg.spec.point, cfg.broker_tz), cfg.in_sample_until)
b = resample_ohlc(b, "5min")
EXITS = {"trailing 1 ATR": Exits(0, 96, trail_atr=1.0), "trailing 2 ATR": Exits(0, 96, trail_atr=2.0),
         "BE 1R + trailing 1 ATR": Exits(0, 96, breakeven_r=1.0, trail_atr=1.0, trail_start_r=1.0),
         "BE 1R + trailing 2 ATR": Exits(0, 96, breakeven_r=1.0, trail_atr=2.0, trail_start_r=1.0),
         "cierre al cruzar EMA20": Exits(0, 96, exit_ema=20)}
rows = []
for (lbm, wick), (en, ex) in itertools.product(itertools.product([120, 480], [0.0, 0.4]), EXITS.items()):
    lb = lbm // 5
    strat = StrategySpec("level_bounce", {"lookback": lb, "gap": max(3, lb // 8), "wick": wick}, [], ex)
    row = {"horas_nivel": lbm / 60, "mecha": wick, "salida": en}
    for lab, data, costs in [("bruto", b.assign(spread=0.0), Costs()), ("neto", b, cfg.costs)]:
        lo, sh, st, _ = build_signals(comps.Context(data, cfg.spec), strat)
        t = run_backtest(data, lo, sh, st, ex, costs)
        r = t["r"].to_numpy(); row[f"exp_{lab}"] = r.mean()
        if lab == "neto":
            bs = stats.bootstrap_mean(r, n_boot=1000)
            pts = (t["exit"] - t["entry"]) * t["side"]
            row.update(n=len(r), acierto=(r > 0).mean(), ci_lo=bs["ci_low"], ci_hi=bs["ci_high"],
                       mejor_op_pts=pts.max(), ganancia_media_pts=pts[pts > 0].mean(), perdida_media_pts=pts[pts <= 0].mean())
    rows.append(row)
pd.set_option("display.width", 250)
df = pd.DataFrame(rows)
print(cfg.spec.symbol, "| netas > 0:", int((df.exp_neto > 0).sum()), "de", len(df))
print(df.sort_values("exp_neto", ascending=False).round(3).to_string(index=False))
