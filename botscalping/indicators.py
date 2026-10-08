"""Indicadores. Regla de oro: el valor en la barra ``i`` solo puede usar información
disponible al CIERRE de la barra ``i`` (las señales se evalúan al cierre y se entra en
la apertura de la siguiente)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def atr(bars: pd.DataFrame, n: int = 14) -> pd.Series:
    prev_close = bars["close"].shift()
    tr = pd.concat(
        [bars["high"] - bars["low"], (bars["high"] - prev_close).abs(), (bars["low"] - prev_close).abs()], axis=1
    ).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def resample_ohlc(bars: pd.DataFrame, rule: str) -> pd.DataFrame:
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "tick_volume": "sum", "spread": "mean"}
    return bars.resample(rule, label="left", closed="left").agg(agg).dropna(subset=["close"])


def align_higher_tf(htf: pd.Series, ltf_index: pd.DatetimeIndex, htf_rule: str, ltf_rule: str = "1min") -> pd.Series:
    """Lleva una serie de marco superior (p. ej. M5) al índice M1 SIN mirar el futuro.

    La barra M5 etiquetada 10:00 cubre 10:00–10:04 y se conoce al cierre de la barra M1
    etiquetada 10:04. Por eso se desplaza ``htf_rule - ltf_rule`` antes del ffill."""
    shifted = htf.copy()
    shifted.index = shifted.index + pd.Timedelta(htf_rule) - pd.Timedelta(ltf_rule)
    return shifted.reindex(ltf_index, method="ffill")


def align_higher_tf_events(htf: pd.Series, ltf_index: pd.DatetimeIndex, htf_rule: str, ltf_rule: str = "1min") -> np.ndarray:
    """Como ``align_higher_tf`` pero para eventos: marca SOLO la barra M1 que cierra la barra
    del marco superior (no se repite la señal en las barras siguientes)."""
    shifted = htf.copy()
    shifted.index = shifted.index + pd.Timedelta(htf_rule) - pd.Timedelta(ltf_rule)
    return shifted.reindex(ltf_index).fillna(False).to_numpy(bool)


def session_frame(index: pd.DatetimeIndex, tz: str, open_time: str) -> pd.DataFrame:
    """Para cada barra: fecha de sesión (anclada en la apertura) y minutos desde la apertura."""
    local = index.tz_convert(tz).tz_localize(None)
    offset = pd.Timedelta(f"{open_time}:00")
    shifted = local - offset
    session_date = shifted.normalize()
    minutes = (shifted - session_date) / pd.Timedelta(minutes=1)
    return pd.DataFrame({"session_date": session_date, "minutes_from_open": minutes.astype(float)}, index=index)


def anchored_vwap(bars: pd.DataFrame, session_date: pd.Series) -> pd.Series:
    typical = (bars["high"] + bars["low"] + bars["close"]) / 3
    vol = bars["tick_volume"].clip(lower=1)
    pv = (typical * vol).groupby(session_date.to_numpy()).cumsum()
    v = vol.groupby(session_date.to_numpy()).cumsum()
    return pv / v


def opening_range(bars: pd.DataFrame, sess: pd.DataFrame, minutes: int) -> pd.DataFrame:
    """Máximo/mínimo de los primeros ``minutes`` de cada sesión. NaN hasta que el rango
    está completo (no se usa el rango mientras se está formando)."""
    in_range = sess["minutes_from_open"] < minutes
    key = sess["session_date"].to_numpy()
    hi = bars["high"].where(in_range).groupby(key).transform("max")
    lo = bars["low"].where(in_range).groupby(key).transform("min")
    ready = sess["minutes_from_open"] >= minutes
    return pd.DataFrame({"or_high": hi.where(ready), "or_low": lo.where(ready)}, index=bars.index)


def swing_levels(bars: pd.DataFrame, k: int = 3) -> pd.DataFrame:
    """Último swing high/low CONFIRMADO (fractal de ``k`` barras a cada lado). Un swing en
    la barra j solo se conoce al cierre de la barra j+k, por eso se desplaza k barras."""
    w = 2 * k + 1
    hi = bars["high"]
    lo = bars["low"]
    is_sh = hi == hi.rolling(w, center=True).max()
    is_sl = lo == lo.rolling(w, center=True).min()
    last_sh = hi.where(is_sh).ffill().shift(k)
    last_sl = lo.where(is_sl).ffill().shift(k)
    return pd.DataFrame({"swing_high": last_sh, "swing_low": last_sl}, index=bars.index)


def bars_since(cond: pd.Series) -> pd.Series:
    """Barras transcurridas desde la última vez que ``cond`` fue cierto (inf si nunca)."""
    pos = np.arange(len(cond), dtype=float)
    last = pd.Series(np.where(cond.to_numpy(), pos, np.nan), index=cond.index).ffill()
    return (pos - last).fillna(np.inf)
