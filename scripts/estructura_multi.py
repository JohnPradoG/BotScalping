# Oro H1+M5 con tendencia H4 a favor, stop 0,5 ATR(H1) bajo el mínimo de H1, objetivo 1:2, permitiendo hasta N
# operaciones abiertas a la vez (cada señal nueva abre otra si hay hueco). Riesgo 20 $ por operación.
# Uso: PYTHONPATH=. python scripts/estructura_multi.py configs/xauusd.toml
import sys, numpy as np, pandas as pd
from botscalping.experiment import load_config
from botscalping.data import load_mt5_csv
from botscalping.indicators import resample_ohlc, atr, ema, align_higher_tf
cfg = load_config(sys.argv[1]); slip = cfg.costs.slippage
raw = load_mt5_csv(cfg.data_path, cfg.spec.point, cfg.broker_tz)
b = resample_ohlc(raw, "5min"); H = resample_ohlc(raw, "1h"); H4 = resample_ohlc(raw, "4h")
cut = pd.Timestamp(cfg.in_sample_until, tz=b.index.tz) if b.index.tz is not None else pd.Timestamp(cfg.in_sample_until)
def swings(x, k=3):
    hi, lo = x["high"], x["low"]; w = 2 * k + 1
    sh = hi.where(hi == hi.rolling(w, center=True).max()).dropna(); sl = lo.where(lo == lo.rolling(w, center=True).min()).dropna()
    f = lambda s: s.reindex(x.index).ffill().shift(k); return f(sh), f(sh.shift(1)), f(sl), f(sl.shift(1))
def trend(x, tf):
    sh, sh0, sl, sl0 = swings(x); e = ema(x["close"], 20)
    up = (sh > sh0) & (sl > sl0) & (x["close"] > e); dn = (sh < sh0) & (sl < sl0) & (x["close"] < e)
    al = lambda s: align_higher_tf(s.astype(float), b.index, tf, "5min"); return al(up) > .5, al(dn) > .5, al(sl), al(sh)
up, dn, hsl, hsh = trend(H, "1h"); up4, dn4, _, _ = trend(H4, "4h")
a, e, c = atr(b), ema(b["close"], 20), b["close"]; aH = align_higher_tf(atr(H), b.index, "1h", "5min")
sh, _, sl, _ = swings(b); rng = (b["high"] - b["low"]).replace(0, np.nan); pos = (c - b["low"]) / rng
L = up & up4 & (c > e) & ((b["low"] <= e + 0.1 * a) | (b["low"] <= sl + 0.25 * a)) & (pos >= 0.6)
S = dn & dn4 & (c < e) & ((b["high"] >= e - 0.1 * a) | (b["high"] >= sh - 0.25 * a)) & (pos <= 0.4)
L &= ~L.shift(fill_value=False); S &= ~S.shift(fill_value=False)
dl = (c - (hsl - 0.1 * a - 0.5 * aH)).clip(lower=0.5 * a); ds = ((hsh + 0.1 * a + 0.5 * aH) - c).clip(lower=0.5 * a)
o, h, l, cl, sp = (b[k].to_numpy(float) for k in ("open", "high", "low", "close", "spread"))
Ln, Sn, DL, DS = L.to_numpy(), S.to_numpy(), dl.to_numpy(), ds.to_numpy(); n = len(b)
def one(i, side, d, rr=2, hold=288):  # una operación independiente desde la señal i
    j = i + 1; en = o[j] + (sp[j] + slip if side == 1 else -slip); stop = en - side * d; tp = en + side * rr * d
    while j < n - 1 and j - i <= hold:
        if side == 1:
            if l[j] <= stop: return j, (min(o[j], stop) - slip - en) / d
            if h[j] >= tp: return j, (tp - en) / d
        else:
            if h[j] + sp[j] >= stop: return j, -(max(o[j] + sp[j], stop) + slip - en) / d
            if l[j] + sp[j] <= tp: return j, -(tp - en) / d
        j += 1
    x = cl[j] - slip if side == 1 else cl[j] + sp[j] + slip
    return j, side * (x - en) / d
sig = [(i, 1, DL[i]) for i in np.where(Ln)[0]] + [(i, -1, DS[i]) for i in np.where(Sn)[0]]
sig = sorted((i, s, d) for i, s, d in sig if np.isfinite(d) and d > 0 and i < n - 2)
for N in [1, 2, 3, 5]:
    open_until, res = [], []
    for i, s, d in sig:
        open_until = [x for x in open_until if x > i]
        if len(open_until) >= N: continue
        j, r = one(i, s, d); open_until.append(j); res.append((b.index[i], r))
    t = pd.Series(dict(res)); usd = 20 * t; eq = 1000 + usd.cumsum()
    ti, to = t[t.index <= cut], t[t.index > cut]
    print(f"{cfg.spec.symbol} máx {N} a la vez | ops {len(t)} ({len(t)/ (b.index.normalize().nunique()):.2f}/día) | in-sample {ti.mean():+.3f}R | OOS {to.mean():+.3f}R | "
          f"total {usd.sum():,.0f} $ | mínimo cuenta {eq.min():,.0f} $ | caída máx {(eq.cummax()-eq).max():,.0f} $ | por año {usd.groupby(usd.index.year).sum().round(0).to_dict()}")
