# Mejoras sobre la candidata "estructura H1 + entrada M5 + stop amplio" (24/5). Cada mejora se elige SOLO con in-sample;
# fuera de muestra se muestra al lado para ver si aguanta. También el resultado en $ arriesgando 20 $ por operación.
# Uso: PYTHONPATH=. python scripts/estructura_mejoras.py configs/xauusd.toml
import sys, numpy as np, pandas as pd
from botscalping.experiment import load_config
from botscalping.data import load_mt5_csv
from botscalping.indicators import resample_ohlc, atr, ema, align_higher_tf
from botscalping import stats
from botscalping.engine import run_backtest, Exits
cfg = load_config(sys.argv[1])
raw = load_mt5_csv(cfg.data_path, cfg.spec.point, cfg.broker_tz)
b = resample_ohlc(raw, "5min"); H = resample_ohlc(raw, "1h"); H4 = resample_ohlc(raw, "4h")
cut = pd.Timestamp(cfg.in_sample_until, tz=b.index.tz) if b.index.tz is not None else pd.Timestamp(cfg.in_sample_until)

def swings(x, k=3):
    hi, lo = x["high"], x["low"]; w = 2 * k + 1
    sh = hi.where(hi == hi.rolling(w, center=True).max()).dropna(); sl = lo.where(lo == lo.rolling(w, center=True).min()).dropna()
    f = lambda s: s.reindex(x.index).ffill().shift(k)
    return f(sh), f(sh.shift(1)), f(sl), f(sl.shift(1))

def trend(x, tf):
    sh, sh0, sl, sl0 = swings(x); e = ema(x["close"], 20)
    up = (sh > sh0) & (sl > sl0) & (x["close"] > e); dn = (sh < sh0) & (sl < sl0) & (x["close"] < e)
    al = lambda s: align_higher_tf(s.astype(float), b.index, tf, "5min")
    return al(up) > .5, al(dn) > .5, al(sl), al(sh)

up, dn, hsl, hsh = trend(H, "1h"); up4, dn4, _, _ = trend(H4, "4h")
a, e, c = atr(b), ema(b["close"], 20), b["close"]
sh, _, sl, _ = swings(b)
rng = (b["high"] - b["low"]).replace(0, np.nan); pos = (c - b["low"]) / rng
vol_ok = b["tick_volume"] > b["tick_volume"].rolling(20).mean()
hr = pd.Series(b.index.hour, index=b.index)  # UTC
L0 = up & (c > e) & ((b["low"] <= e + 0.1 * a) | (b["low"] <= sl + 0.25 * a)) & (pos >= 0.6)
S0 = dn & (c < e) & ((b["high"] >= e - 0.1 * a) | (b["high"] >= sh - 0.25 * a)) & (pos <= 0.4)
dl = (c - (hsl - 0.1 * a)).clip(lower=0.5 * a); ds = ((hsh + 0.1 * a) - c).clip(lower=0.5 * a)
VARS = {"base (24/5)": (L0, S0), "+ tendencia H4 a favor": (L0 & up4, S0 & dn4), "+ volumen > media": (L0 & vol_ok, S0 & vol_ok),
        "+ stop no más de 3 ATR(M5)": (L0 & (dl <= 3 * a), S0 & (ds <= 3 * a)), "solo 7-20 h UTC (Londres+NY)": (L0 & hr.between(7, 19), S0 & hr.between(7, 19))}
EX = {"1:1": Exits(1, 288), "1:2": Exits(2, 288), "BE 1R + trailing 2ATR": Exits(0, 288, breakeven_r=1.0, trail_atr=2.0, trail_start_r=1.0)}
rows = []; best = None
for vn, (L, S) in VARS.items():
    L = L & ~L.shift(fill_value=False); S = S & ~S.shift(fill_value=False)
    stop = dl.where(L, ds.where(S)).to_numpy(float)
    for en, ex in EX.items():
        t = run_backtest(b, L.to_numpy(), S.to_numpy(), stop, ex, cfg.costs)
        ti, to = t[t.entry_time <= cut], t[t.entry_time > cut]
        rows.append(dict(variante=vn, salida=en, n_is=len(ti), exp_is=ti.r.mean(), p_is=stats.bootstrap_mean(ti.r.to_numpy(), n_boot=1000)["p_gt_0"],
                         años_is=f"{int((ti.groupby(ti.entry_time.dt.year).r.mean()>0).sum())}/{ti.entry_time.dt.year.nunique()}",
                         n_oos=len(to), exp_oos=to.r.mean(), usd_20_total=20 * t.r.sum(), ops_dia=len(t) / (b.index.normalize().nunique()),
                         stop_med=t.risk.median()))
        rows[-1]["_t"] = t
df = pd.DataFrame(rows); pd.set_option("display.width", 250)
print(f"## {cfg.spec.symbol}: H1 + M5, stop bajo el mínimo de H1 (elegir por exp_is; exp_oos solo para ver si aguanta)")
print(df.drop(columns="_t").sort_values("exp_is", ascending=False).round(3).to_string(index=False))
w = df.sort_values("exp_is", ascending=False).iloc[0]; t = w["_t"]
usd = 20 * t.r; eq = 1000 + usd.cumsum().to_numpy()
print(f"\nMejor in-sample: {w.variante} | {w.salida} -> con 20 $ por operación desde 1.000 $: total {usd.sum():,.0f} $, "
      f"mínimo de la cuenta {eq.min():,.0f} $, caída máx {(np.maximum.accumulate(eq)-eq).max():,.0f} $, "
      f"por año {usd.groupby(t.entry_time.dt.year).sum().round(0).to_dict()}")
