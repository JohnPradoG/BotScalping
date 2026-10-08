# Tres estrategias públicas (TradingView), con sus reglas tal cual, sobre los datos de Exness con costes reales.
#  1) "RSI Scalping Gold (XAUUSD) v5": scalping a favor de tendencia (RSI cruza 30/70 + EMA9/SMA20/SMA200 + volumen relativo).
#  2) "Reversion Guard RSI + Bollinger": rango/reversión (cierre fuera de Bollinger 20,2 con RSI extremo, salida en la media).
#  3) "NQ Phantom Scalper Pro": rango/reversión a la VWAP de la sesión (toca banda de VWAP con pico de volumen, salida en la VWAP).
# Señal al cierre, entrada en la apertura siguiente, stop ATR intrabarra, salidas por condición en la apertura siguiente.
# Uso: PYTHONPATH=. python scripts/estrategias_web.py configs/nas100.toml
import sys, numpy as np, pandas as pd
from botscalping.experiment import load_config
from botscalping.data import load_mt5_csv
from botscalping.indicators import resample_ohlc, atr, ema
from botscalping import stats
cfg = load_config(sys.argv[1]); slip = cfg.costs.slippage
raw = load_mt5_csv(cfg.data_path, cfg.spec.point, cfg.broker_tz)
cut = pd.Timestamp(cfg.in_sample_until, tz="UTC") if raw.index.tz is not None else pd.Timestamp(cfg.in_sample_until)

def rsi(c, n=14):
    d = c.diff(); up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean(); dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)

def sim(b, L, S, XL, XS, sd, hold):
    o, h, l, cl, sp = (b[k].to_numpy(float) for k in ("open", "high", "low", "close", "spread"))
    L, S, XL, XS, sd = map(np.asarray, (L, S, XL, XS, sd)); n = len(b); out = []; i = 0
    while i < n - 2:
        side = 1 if L[i] else (-1 if S[i] else 0)
        if side == 0 or not np.isfinite(sd[i]) or sd[i] <= 0: i += 1; continue
        j = i + 1; e = o[j] + (sp[j] + slip if side == 1 else -slip); stop = e - side * sd[i]; x = None
        while j < n - 1:
            if side == 1 and l[j] <= stop: x = min(o[j], stop) - slip if j > i + 1 else stop - slip; break
            if side == -1 and h[j] + sp[j] >= stop: x = max(o[j] + sp[j], stop) + slip if j > i + 1 else stop + slip; break
            if (XL[j] if side == 1 else XS[j]) or j - i >= hold:
                x = o[j + 1] - slip if side == 1 else o[j + 1] + sp[j + 1] + slip; j += 1; break
            j += 1
        if x is None: break
        out.append((b.index[i], side * (x - e) / sd[i])); i = j
    return pd.Series(dict(out), dtype=float)

def report(name, tf, r):
    for lab, g in [("in-sample", r[r.index <= cut]), ("OOS", r[r.index > cut])]:
        if len(g) < 10: print(f"  {name:<34} {tf:>5} {lab:<9} n={len(g)}"); continue
        bs = stats.bootstrap_mean(g.to_numpy(), n_boot=1000)
        print(f"  {name:<34} {tf:>5} {lab:<9} n={len(g):>5} exp={g.mean():+.3f}R IC=[{bs['ci_low']:+.3f},{bs['ci_high']:+.3f}] "
              f"acierto={(g>0).mean():.0%} años+={int((g.groupby(g.index.year).mean()>0).sum())}/{g.index.year.nunique()}")

print(f"## {cfg.spec.symbol}")
for tf in ["5min", "15min"]:
    b = resample_ohlc(raw, tf); c = b["close"]; a = atr(b); R = rsi(c)
    ny = b.index.tz_localize("UTC").tz_convert("America/New_York") if b.index.tz is None else b.index.tz_convert("America/New_York")
    hr = pd.Series(ny.hour + ny.minute / 60, index=b.index)
    # 1) RSI Scalping Gold v5
    e9, s20, s200 = ema(c, 9), c.rolling(20).mean(), c.rolling(200).mean()
    rvol = b["tick_volume"] / b["tick_volume"].rolling(20).mean()
    L = (R.shift() <= 30) & (R > 30) & (c > e9) & (e9 > s20) & (c > s200) & (rvol >= 1.25)
    S = (R.shift() >= 70) & (R < 70) & (c < e9) & (e9 < s20) & (c < s200) & (rvol >= 1.25)
    XL = ((R.shift() >= 70) & (R < 70)) | ((e9.shift() >= s20.shift()) & (e9 < s20))
    XS = ((R.shift() <= 30) & (R > 30)) | ((e9.shift() <= s20.shift()) & (e9 > s20))
    report("1 Scalping RSI+EMA (tendencia)", tf, sim(b, L, S, XL, XS, (1.5 * a).to_numpy(), 96))
    # 1b) tal cual casi nunca dispara (RSI saliendo de 30 con EMA9 > SMA20 es casi contradictorio): versión relajada sin EMA9 > SMA20
    L = (R.shift() <= 30) & (R > 30) & (c > e9) & (c > s200) & (rvol >= 1.25)
    S = (R.shift() >= 70) & (R < 70) & (c < e9) & (c < s200) & (rvol >= 1.25)
    report("1b Scalping RSI+EMA relajada", tf, sim(b, L, S, XL, XS, (1.5 * a).to_numpy(), 96))
    # 2) Reversion Guard: Bollinger 20,2 + RSI 30/70, salida en la media, stop 2 ATR
    m, sdv = c.rolling(20).mean(), c.rolling(20).std()
    L = (c < m - 2 * sdv) & (R < 30); S = (c > m + 2 * sdv) & (R > 70)
    report("2 Rango Bollinger+RSI -> media", tf, sim(b, L, S, c >= m, c <= m, (2 * a).to_numpy(), 96))
    # 3) NQ Phantom: VWAP de sesión (09:30 NY) con bandas 2σ, pico de volumen 1.5x, 9-16 h NY sin 12-14, salida en VWAP
    day = pd.Series(ny.date, index=b.index); sess = (hr >= 9.5) & (hr < 16)
    tp = (b["high"] + b["low"] + c) / 3; v = b["tick_volume"].where(sess, 0).astype(float)
    g = day.values
    cv = v.groupby(g).cumsum(); vw = (tp * v).groupby(g).cumsum() / cv
    var = ((tp ** 2) * v).groupby(g).cumsum() / cv - vw ** 2; sd_vw = np.sqrt(var.clip(lower=0))
    ok = sess & (hr >= 9.75) & ~((hr >= 12) & (hr < 14)) & (b["tick_volume"] > 1.5 * b["tick_volume"].rolling(20).mean())
    L = ok & (b["low"] <= vw - 2 * sd_vw) & (c > vw - 2 * sd_vw)
    S = ok & (b["high"] >= vw + 2 * sd_vw) & (c < vw + 2 * sd_vw)
    report("3 Rango VWAP bandas -> VWAP", tf, sim(b, L, S, (c >= vw) | ~sess, (c <= vw) | ~sess, (1.5 * a).to_numpy(), 96))
