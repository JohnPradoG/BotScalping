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
def one(i, side, d, rr=2, hold=288, be=0.0):  # una operación independiente desde la señal i
    j = i + 1; en = o[j] + (sp[j] + slip if side == 1 else -slip); stop = en - side * d; tp = en + side * rr * d
    while j < n - 1 and j - i <= hold:
        if be and stop != en and side * (cl[j - 1] - en) >= be * d and j > i + 1: stop = en
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
day = b.index.normalize()
def run(maxN=1000, gap=0, be=0.0, pause_losses=0, max_same_dir=1000):
    opened, res, last_entry = [], [], {1: -10**9, -1: -10**9}
    closed = []  # (índice de cierre, R): solo se usa lo ya cerrado antes de la señal (sin mirar el futuro)
    for i, s, d in sig:
        opened = [x for x in opened if x[0] > i]
        if len(opened) >= maxN or sum(1 for x in opened if x[1] == s) >= max_same_dir: continue
        if i - last_entry[s] < gap: continue
        if pause_losses and sum(1 for jj, rr in closed if jj < i and day[jj] == day[i] and rr < 0) >= pause_losses: continue
        j, r = one(i, s, d, be=be); opened.append((j, s)); last_entry[s] = i; res.append((b.index[i], r))
        if pause_losses: closed = [x for x in closed if day[x[0]] >= day[i]] + [(j, r)]
    t = pd.Series(dict(res)); Rc = t.cumsum(); dd = (Rc.cummax() - Rc).max()
    return t, dd
rows = []
for name, kw in {"sin límite": {}, "máx 3": {"maxN": 3}, "máx 2 por dirección": {"max_same_dir": 2},
                 "separación 1 h entre entradas": {"gap": 12}, "separación 4 h": {"gap": 48},
                 "break-even al ir +1R": {"be": 1.0}, "pausa el día tras 3 pérdidas cerradas": {"pause_losses": 3}, "pausa tras 2 pérdidas": {"pause_losses": 2},
                 "sep. 1 h + BE 1R + máx 2 por dir.": {"gap": 12, "be": 1.0, "max_same_dir": 2}}.items():
    t, dd = run(**kw); ti, to = t[t.index <= cut], t[t.index > cut]
    risk = 350 / dd  # $ por operación para que la peor racha sea 350 $ (35 % de 1.000 $)
    rows.append(dict(ajuste=name, ops=len(t), R_total=t.sum(), peor_racha_R=dd, ganancia_por_racha=t.sum() / dd,
                     is_R=ti.mean(), oos_R=to.mean(), riesgo_para_1000=risk, ganancia_1000=risk * t.sum(), a20_total=20 * t.sum(), a20_racha=20 * dd))
pd.set_option("display.width", 250)
print(pd.DataFrame(rows).round(3).to_string(index=False))
