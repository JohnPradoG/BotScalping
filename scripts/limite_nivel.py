"""Entrar JUSTO en el nivel con orden límite (idea de John: "entrar donde se da vuelta").

Nivel = mínimo/máximo de las últimas `horas` (sin las últimas `gap` velas), que ha aguantado.
Compra límite en el soporte: se llena solo si el ASK llega al nivel (bid low <= nivel - spread),
es decir, el precio cotiza a través del nivel. Stop a `sl` ATR(M5) por debajo; objetivo `rr`·stop.
Si en la vela de llenado también se toca el stop, cuenta como stop (conservador).
Una sola entrada por nivel; simétrico en resistencias.
Uso: PYTHONPATH=. python scripts/limite_nivel.py configs/nas100.toml
"""
import sys, itertools, numpy as np, pandas as pd
from botscalping.experiment import load_config
from botscalping.data import load_mt5_csv, split_by_date
from botscalping import indicators as ind, stats

cfg = load_config(sys.argv[1])
b, _ = split_by_date(load_mt5_csv(cfg.data_path, cfg.spec.point, cfg.broker_tz), cfg.in_sample_until)
atr5 = ind.align_higher_tf(ind.atr(ind.resample_ohlc(b, "5min")), b.index, "5min").to_numpy()
o, h, l, c = (b[k].to_numpy() for k in ("open", "high", "low", "close"))
slip = cfg.costs.slippage


def simulate(sup, res, sl_atr, rr, spread, max_bars=240):
    n = len(c); out = []; i = 1; last_level = (np.nan, np.nan)
    while i < n - 1:
        s, r_, a = sup[i], res[i], atr5[i - 1]
        if not np.isfinite(a) or a <= 0:
            i += 1; continue
        side = 0
        if np.isfinite(s) and l[i] <= s - spread[i] and l[i - 1] > s and s != last_level[0]:
            side, entry, last_level = 1, s, (s, last_level[1])
        elif np.isfinite(r_) and h[i] >= r_ and h[i - 1] < r_ and r_ != last_level[1]:
            side, entry, last_level = -1, r_, (last_level[0], r_)
        if side == 0:
            i += 1; continue
        d = sl_atr * a
        sl = entry - side * d; tp = entry + side * rr * d
        j = i; px = None
        while j < min(n, i + max_bars):
            lo_b = l[j] if side == 1 else l[j] + spread[j]   # long sale al bid; short recompra al ask
            hi_b = h[j] if side == 1 else h[j] + spread[j]
            if side == 1:
                if lo_b <= sl: px = sl - slip; break
                if j > i and hi_b >= tp: px = tp; break
            else:
                if hi_b >= sl: px = sl + slip; break
                if j > i and lo_b <= tp: px = tp; break
            j += 1
        if px is None:
            j = min(n - 1, j); px = c[j] if side == 1 else c[j] + spread[j]
        out.append(((px - entry) * side) / d)
        i = j + 1
    return np.array(out)


rows = []
spr_net = b["spread"].to_numpy(); spr0 = np.zeros_like(spr_net)
for horas in [2, 8]:
    lb, gap = horas * 60, max(15, horas * 60 // 8)
    sup = b["low"].shift(gap).rolling(lb - gap).min().to_numpy()
    res = b["high"].shift(gap).rolling(lb - gap).max().to_numpy()
    # aguantó HASTA la vela anterior (la vela del llenado aún no ha cerrado: no se puede usar su cierre)
    held_s = b["close"].shift(1).rolling(gap).min().to_numpy() > sup
    held_r = b["close"].shift(1).rolling(gap).max().to_numpy() < res
    sup = np.where(held_s, sup, np.nan); res = np.where(held_r, res, np.nan)
    for sl_atr, rr in itertools.product([0.5, 1.0, 2.0], [1.0, 2.0]):
        row = {"horas_nivel": horas, "stop_atrM5": sl_atr, "rr": rr}
        for lab, spr in [("bruto", spr0), ("neto", spr_net)]:
            r = simulate(sup, res, sl_atr, rr, spr)
            row[f"exp_{lab}"] = r.mean()
            if lab == "neto":
                bs = stats.bootstrap_mean(r, n_boot=1000)
                row.update(n=len(r), acierto=(r > 0).mean(), ci_lo=bs["ci_low"], ci_hi=bs["ci_high"])
        rows.append(row)
        print(row, file=sys.stderr, flush=True)
pd.set_option("display.width", 250)
print(cfg.spec.symbol, "— orden límite en el nivel (R por operación)")
print(pd.DataFrame(rows).round(3).to_string(index=False))
