"""Métricas y pruebas estadísticas (solo numpy, sin supuestos de normalidad)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def summary(r: np.ndarray) -> dict:
    r = np.asarray(r, float)
    n = len(r)
    if n == 0:
        return {"n": 0, "win_rate": np.nan, "expectancy_r": np.nan, "profit_factor": np.nan,
                "total_r": 0.0, "max_dd_r": 0.0, "sharpe_trade": np.nan}
    equity = np.cumsum(r)
    dd = np.maximum.accumulate(np.r_[0.0, equity])[1:] - equity
    gains, losses = r[r > 0].sum(), -r[r < 0].sum()
    return {
        "n": n,
        "win_rate": float((r > 0).mean()),
        "expectancy_r": float(r.mean()),
        "profit_factor": float(gains / losses) if losses > 0 else np.inf,
        "total_r": float(equity[-1]),
        "max_dd_r": float(dd.max()),
        "sharpe_trade": float(r.mean() / r.std(ddof=1)) if n > 1 and r.std(ddof=1) > 0 else np.nan,
    }


def bootstrap_mean(r: np.ndarray, n_boot: int = 5000, alpha: float = 0.05, seed: int = 0) -> dict:
    """IC bootstrap de la expectativa y p-valor unilateral de H0: expectativa <= 0."""
    r = np.asarray(r, float)
    if len(r) < 2:
        return {"ci_low": np.nan, "ci_high": np.nan, "p_gt_0": np.nan}
    rng = np.random.default_rng(seed)
    chunk = max(1, 2_000_000 // len(r))  # acota memoria con muestras grandes
    means = np.concatenate([
        r[rng.integers(0, len(r), (min(chunk, n_boot - k), len(r)))].mean(axis=1) for k in range(0, n_boot, chunk)
    ])
    centered = means - r.mean()  # distribución bajo H0 (media 0)
    p = float((centered >= r.mean()).mean())
    lo, hi = np.quantile(means, [alpha / 2, 1 - alpha / 2])
    return {"ci_low": float(lo), "ci_high": float(hi), "p_gt_0": max(p, 1 / n_boot)}


def permutation_diff(a: np.ndarray, b: np.ndarray, n_perm: int = 5000, seed: int = 0) -> dict:
    """¿La media de ``a`` es mayor que la de ``b``? Test de permutación unilateral.

    Uso típico: a = operaciones que un filtro CONSERVA, b = las que ELIMINA. Si el filtro
    aporta valor, las eliminadas deben ser significativamente peores."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 2 or len(b) < 2:
        return {"diff": np.nan, "p_value": np.nan}
    obs = a.mean() - b.mean()
    pooled = np.r_[a, b]
    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(n_perm):
        rng.shuffle(pooled)
        count += pooled[: len(a)].mean() - pooled[len(a):].mean() >= obs
    return {"diff": float(obs), "p_value": (count + 1) / (n_perm + 1)}


def holm(pvalues: list[float]) -> list[float]:
    """Corrección de Holm-Bonferroni: al probar muchos componentes, alguno 'funciona' por azar."""
    p = np.asarray(pvalues, float)
    out = np.full_like(p, np.nan)
    ok = ~np.isnan(p)
    idx = np.flatnonzero(ok)
    order = idx[np.argsort(p[ok])]
    m = len(order)
    running = 0.0
    for rank, k in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p[k]))
        out[k] = running
    return out.tolist()


def tag_trades(trades: pd.DataFrame, allow_long: np.ndarray, allow_short: np.ndarray) -> np.ndarray:
    """Para cada operación: ¿la habría permitido este filtro en su barra de señal?"""
    if trades.empty:
        return np.zeros(0, bool)
    i = trades["signal_idx"].to_numpy(int)
    side = trades["side"].to_numpy(int)
    return np.where(side == 1, allow_long[i], allow_short[i])


def by_period(trades: pd.DataFrame, freq: str = "QE") -> pd.DataFrame:
    """Expectativa por periodo: una ventaja real debería ser estable, no venir de un mes."""
    if trades.empty:
        return pd.DataFrame()
    g = trades.set_index("entry_time")["r"].groupby(pd.Grouper(freq=freq))
    return pd.DataFrame({"n": g.size(), "expectancy_r": g.mean(), "total_r": g.sum()})
