# Idea de John: SOLO compras. Esperar una caída, que llegue a un soporte y deje vela de rechazo, y comprar.
# Se compara con comprar al azar con la misma salida (eso mide cuánto es simplemente "estar comprado").
# Uso: PYTHONPATH=. python scripts/solo_compras.py configs/nas100.toml [--validate]
import sys, itertools, numpy as np, pandas as pd
from botscalping.experiment import load_config
from botscalping.data import load_mt5_csv, split_by_date
from botscalping.indicators import resample_ohlc, atr
from botscalping import components as comps, stats
from botscalping.engine import StrategySpec, build_signals, run_backtest, Exits
cfg = load_config(sys.argv[1]); oos = "--validate" in sys.argv
is_b, oos_b = split_by_date(load_mt5_csv(cfg.data_path, cfg.spec.point, cfg.broker_tz), cfg.in_sample_until)
base = oos_b if oos else is_b
HOLD = {"5min": 288, "15min": 96, "1h": 120}
EXITS = {"1:1": (1, 0, 0, 0), "1:2": (2, 0, 0, 0), "trailing 1ATR": (0, 0, 1.0, 0), "BE 1R + trailing 2ATR": (0, 1.0, 2.0, 1.0)}
rows = []
for tf in HOLD:
    b = resample_ohlc(base, tf); ctx = comps.Context(b, cfg.spec); a = atr(b)
    rng = (b["high"] - b["low"]).replace(0, np.nan)
    rechazo = ((b["close"] - b["low"]) / rng >= 0.66).to_numpy()
    for (en, (rr, be, tr, ts)), caida, k in itertools.product(EXITS.items(), [2.0, 3.0], [3, 5]):
        ex = Exits(rr, HOLD[tf], breakeven_r=be, trail_atr=tr, trail_start_r=ts)
        cayo = ((b["high"].rolling(12).max() - b["close"]) >= caida * a).to_numpy()
        lo, _, st, _ = build_signals(ctx, StrategySpec("sr_bounce", {"k": k}, [], ex))
        lo = lo & cayo & rechazo
        t = run_backtest(b, lo, np.zeros_like(lo), st, ex, cfg.costs)
        r = t["r"].to_numpy()
        if len(r) < 20: continue
        # azar: mismas horas no, mismo nº aproximado de compras, stop 1,5 ATR
        rl, _, rst, _ = build_signals(ctx, StrategySpec("random", {"prob": len(r) / len(b), "sl_atr": 1.5}, [], ex))
        ra = run_backtest(b, rl, np.zeros_like(rl), rst, ex, cfg.costs)["r"].to_numpy()
        bs = stats.bootstrap_mean(r, n_boot=1000)
        yr = t.groupby(t["entry_time"].dt.year)["r"].mean()
        rows.append(dict(tf=tf, caida_atr=caida, k=k, salida=en, n=len(r), exp_r=r.mean(), ci_lo=bs["ci_low"], ci_hi=bs["ci_high"],
                         acierto=(r > 0).mean(), años_pos=f"{int((yr > 0).sum())}/{len(yr)}", azar_r=ra.mean(),
                         coste_r=np.nanmean((b["spread"].reindex(t["entry_time"]).to_numpy() + 2 * cfg.costs.slippage) / t["risk"].to_numpy())))
df = pd.DataFrame(rows); pd.set_option("display.width", 250)
bh = base["close"].iloc[-1] / base["close"].iloc[0] - 1
print(f"{cfg.spec.symbol} {'OOS' if oos else 'in-sample'} | comprar y mantener {bh:+.1%} | netas>0: {int((df.exp_r>0).sum())}/{len(df)} | "
      f"mejores que el azar: {int((df.exp_r>df.azar_r).sum())}/{len(df)}")
print(df.sort_values("ci_lo", ascending=False).round(3).to_string(index=False))
