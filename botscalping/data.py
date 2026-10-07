"""Carga de datos y especificación de instrumentos.

Convención interna: DataFrame indexado por la hora de APERTURA de cada barra, en UTC,
con columnas ``open high low close tick_volume spread``. Precios bid; ``spread`` en
unidades de precio (no en puntos).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

BAR_COLUMNS = ["open", "high", "low", "close", "tick_volume", "spread"]


@dataclass(frozen=True)
class InstrumentSpec:
    symbol: str
    point: float  # tamaño de 1 punto en precio (XAUUSD suele ser 0.01, NAS100 0.01 o 0.1 según bróker)
    session_tz: str = "America/New_York"
    session_open: str = "09:30"  # apertura de referencia (VWAP anclado, Opening Range, horario)


def load_mt5_csv(path: str, point: float, broker_tz: str = "UTC") -> pd.DataFrame:
    """Lee un CSV exportado desde MetaTrader 5 y lo normaliza al formato interno."""
    raw = pd.read_csv(path, sep=None, engine="python")
    raw.columns = [c.strip().strip("<>").lower() for c in raw.columns]
    if "date" in raw.columns and "time" in raw.columns:
        ts = pd.to_datetime(raw["date"].astype(str) + " " + raw["time"].astype(str), format="mixed")
    else:
        ts = pd.to_datetime(raw[raw.columns[0]], format="mixed")
    ts = pd.DatetimeIndex(ts).tz_localize(broker_tz, ambiguous="NaT", nonexistent="NaT").tz_convert("UTC")
    bars = pd.DataFrame(
        {
            "open": raw["open"].to_numpy(float),
            "high": raw["high"].to_numpy(float),
            "low": raw["low"].to_numpy(float),
            "close": raw["close"].to_numpy(float),
            "tick_volume": raw.get("tickvol", raw.get("tick_volume", pd.Series(0, index=raw.index))).to_numpy(float),
            "spread": raw.get("spread", pd.Series(0, index=raw.index)).to_numpy(float) * point,
        },
        index=ts,
    )
    bars = bars[bars.index.notna()]
    bars = bars[~bars.index.duplicated(keep="first")].sort_index()
    return bars


def synthetic_bars(n: int = 20_000, seed: int = 0, start: str = "2025-01-02 00:00", spread: float = 0.2) -> pd.DataFrame:
    """Barras M1 sintéticas (paseo aleatorio, SIN ventaja real). Sirven para tests y para
    comprobar que el pipeline no inventa expectativa positiva donde no la hay."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start, periods=n, freq="1min", tz="UTC")
    vol = 0.5 * (1 + 0.5 * np.sin(np.arange(n) / 600))
    close = 2000 + np.cumsum(rng.normal(0, vol))
    open_ = np.r_[close[0], close[:-1]]
    wick = np.abs(rng.normal(0, vol, (2, n)))
    high = np.maximum(open_, close) + wick[0]
    low = np.minimum(open_, close) - wick[1]
    return pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "tick_volume": rng.integers(50, 500, n).astype(float),
            "spread": np.full(n, spread),
        },
        index=idx,
    )


def split_by_date(bars: pd.DataFrame, in_sample_until: str | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separa in-sample (para decidir) y out-of-sample (solo para validar, una vez)."""
    if not in_sample_until:
        return bars, bars.iloc[0:0]
    cut = pd.Timestamp(in_sample_until, tz="UTC") + pd.Timedelta(days=1)
    return bars[bars.index < cut], bars[bars.index >= cut]
