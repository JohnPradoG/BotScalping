# Entradas al azar 1:1 arriesgando 20 $ por operación (lote ajustado al stop), cuenta de 1.000 $. M5, 24/5.
# Uso: PYTHONPATH=. python scripts/azar_1a1.py configs/nas100.toml
import sys, numpy as np, pandas as pd
from botscalping.experiment import load_config
from botscalping.data import load_mt5_csv
from botscalping.indicators import resample_ohlc
from botscalping.engine import run_backtest, Exits
cfg = load_config(sys.argv[1])
b = resample_ohlc(load_mt5_csv(cfg.data_path, cfg.spec.point, cfg.broker_tz), "5min")
stops = [4, 10, 20, 50] if "NAS" in cfg.spec.symbol else [1, 2, 4, 10]  # en precio (puntos NAS / dólares de oro)
for st in stops:
    res = []
    for seed in range(20):
        rng = np.random.default_rng(seed); hit = rng.random(len(b)) < 0.01; side = rng.random(len(b)) < .5
        t = run_backtest(b, hit & side, hit & ~side, np.full(len(b), float(st)), Exits(1, 288), cfg.costs)
        usd = 20 * t["r"].to_numpy(); eq = 1000 + np.cumsum(usd)
        res.append((len(usd), (usd > 0).mean(), usd.sum(), (eq <= 0).any(), np.argmax(eq <= 0) if (eq <= 0).any() else -1))
    r = pd.DataFrame(res, columns=["n", "acierto", "total", "quemada", "op_quema"])
    print(f"{cfg.spec.symbol} stop {st:>3} | ops/simulación {r.n.mean():.0f} | acierto {r.acierto.mean():.1%} | resultado medio {r.total.mean():,.0f} $ "
          f"| mejor {r.total.max():,.0f} $ | cuentas quemadas {int(r.quemada.sum())}/20 (en la op ~{r.op_quema[r.quemada].median():.0f})")
