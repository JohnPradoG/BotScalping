# RSI-2 diario NAS100 en dólares con lote fijo. Uso: PYTHONPATH=. python scripts/rsi2_dinero.py configs/nas100.toml 0.05 1000
import sys, numpy as np, pandas as pd
from botscalping.experiment import load_config
from botscalping.data import load_mt5_csv
cfg = load_config(sys.argv[1]); LOT = float(sys.argv[2]); CAP = float(sys.argv[3]); SWAP = 0.0002
b = load_mt5_csv(cfg.data_path, cfg.spec.point, cfg.broker_tz)
ny = b.tz_localize("UTC").tz_convert("America/New_York") if b.index.tz is None else b.tz_convert("America/New_York")
ny = ny[ny.index.dayofweek < 5]
d = ny.between_time("09:30", "15:59").resample("1D").agg({"open": "first", "low": "min", "close": "last", "spread": "last"}).dropna()
c = d["close"]; ch = c.diff()
up = ch.clip(lower=0).ewm(alpha=.5, adjust=False).mean(); dn = (-ch.clip(upper=0)).ewm(alpha=.5, adjust=False).mean()
r2 = 100 - 100 / (1 + up / dn); ma200, ma5 = c.rolling(200).mean(), c.rolling(5).mean()
tr, i = [], 0
while i < len(d) - 1:
    if r2.iloc[i] < 20 and c.iloc[i] > ma200.iloc[i]:
        j = i + 1
        while j < len(d) - 1 and c.iloc[j] <= ma5.iloc[j] and j - i < 10: j += 1
        e = c.iloc[i] + d["spread"].iloc[i] + cfg.costs.slippage; x = c.iloc[j] - cfg.costs.slippage
        worst = d["low"].iloc[i + 1:j + 1].min() - e
        tr.append(dict(entrada=d.index[i].date(), salida=d.index[j].date(), precio=round(e, 1), puntos=x - e - SWAP * e * (j - i), peor_flotante=worst))
        i = j
    i += 1
t = pd.DataFrame(tr)
print(f"operaciones={len(t)} desde {t.entrada.iloc[0]} | puntos totales={t.puntos.sum():.0f} | media={t.puntos.mean():.0f} | "
      f"peor op={t.puntos.min():.0f} | peor flotante={t.peor_flotante.min():.0f} pts | precio medio={t.precio.mean():.0f}")
for cs in [1, 10, 100]:
    usd = t.puntos * LOT * cs; eq = CAP + usd.cumsum()
    print(f"contrato {cs:>3}: ${LOT*cs:.2f}/punto -> ganancia {usd.sum():,.0f} $ | final {eq.iloc[-1]:,.0f} $ | peor op {usd.min():,.0f} $ | "
          f"peor flotante {t.peor_flotante.min()*LOT*cs:,.0f} $ | por año {usd.groupby(pd.to_datetime(t.entrada).dt.year).sum().round(0).to_dict()}")
print(t.tail(5).round(1).to_string(index=False))
