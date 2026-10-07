"""Componentes intercambiables de la estrategia.

Hay dos tipos:

* **setup**: genera las entradas candidatas (dirección + distancia de stop). Exactamente uno
  por estrategia. El *baseline* es un setup sin ningún filtro.
* **filter**: devuelve, barra a barra, si se PERMITE operar en largo y/o en corto. Un filtro
  nunca crea operaciones, solo elimina candidatas. Así se puede medir exactamente qué
  operaciones quita y si las que quita eran peores que las que deja.

Cada componente se registra con un nombre y parámetros por defecto, y se activa o desactiva
desde el fichero de configuración, sin tocar código.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd

from . import indicators as ind
from .data import InstrumentSpec

LongShort = tuple[np.ndarray, np.ndarray]


class Context:
    """Barras + caché de indicadores compartidos entre componentes."""

    def __init__(self, bars: pd.DataFrame, spec: InstrumentSpec):
        self.bars = bars
        self.spec = spec
        self._cache: dict = {}

    def cached(self, key, fn):
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]

    def atr(self, n: int = 14) -> pd.Series:
        return self.cached(("atr", n), lambda: ind.atr(self.bars, n))

    def ema(self, n: int) -> pd.Series:
        return self.cached(("ema", n), lambda: ind.ema(self.bars["close"], n))

    def session(self) -> pd.DataFrame:
        return self.cached(
            "session", lambda: ind.session_frame(self.bars.index, self.spec.session_tz, self.spec.session_open)
        )


@dataclass(frozen=True)
class Component:
    name: str
    kind: str  # "setup" | "filter"
    fn: Callable
    defaults: dict = field(default_factory=dict)
    description: str = ""


REGISTRY: dict[str, Component] = {}


def register(name: str, kind: str, description: str, **defaults):
    def deco(fn):
        REGISTRY[name] = Component(name, kind, fn, defaults, description)
        return fn

    return deco


def get(name: str) -> Component:
    if name not in REGISTRY:
        raise KeyError(f"Componente desconocido '{name}'. Disponibles: {sorted(REGISTRY)}")
    return REGISTRY[name]


def _arr(s: pd.Series) -> np.ndarray:
    return s.fillna(False).to_numpy(bool)


# --------------------------------------------------------------------------- setups
@register("breakout", "setup", "Baseline: cierre rompe el máximo/mínimo de las N barras previas del marco `tf`; stop = sl_atr·ATR(tf).", lookback=5, sl_atr=1.0, tf="1min")
def setup_breakout(ctx: Context, lookback: int, sl_atr: float, tf: str):
    if pd.Timedelta(tf) == pd.Timedelta("1min"):
        b = ctx.bars
        prev_hi = b["high"].rolling(lookback).max().shift()
        prev_lo = b["low"].rolling(lookback).min().shift()
        stop = (ctx.atr() * sl_atr).to_numpy()
        return _arr(b["close"] > prev_hi), _arr(b["close"] < prev_lo), stop
    # Marco superior: la señal se evalúa al cierre de la barra de `tf` y se entra en la siguiente M1.
    htf = ind.resample_ohlc(ctx.bars, tf)
    prev_hi = htf["high"].rolling(lookback).max().shift()
    prev_lo = htf["low"].rolling(lookback).min().shift()
    long_ = ind.align_higher_tf_events(htf["close"] > prev_hi, ctx.bars.index, tf)
    short_ = ind.align_higher_tf_events(htf["close"] < prev_lo, ctx.bars.index, tf)
    stop = (ind.align_higher_tf(ind.atr(htf), ctx.bars.index, tf) * sl_atr).to_numpy()
    return long_, short_, stop


@register("random", "setup", "Benchmark: entradas al azar con la misma gestión. Si un setup no le gana, no tiene ventaja.", prob=0.02, sl_atr=1.0, seed=0, tf="1min")
def setup_random(ctx: Context, prob: float, sl_atr: float, seed: int, tf: str):
    rng = np.random.default_rng(seed)
    n = len(ctx.bars)
    hit = rng.random(n) < prob
    side = rng.random(n) < 0.5
    if pd.Timedelta(tf) == pd.Timedelta("1min"):
        atr = ctx.atr()
    else:
        atr = ind.align_higher_tf(ind.atr(ind.resample_ohlc(ctx.bars, tf)), ctx.bars.index, tf)
    stop = (atr * sl_atr).to_numpy()
    return hit & side, hit & ~side, stop


def _atr_tf(ctx: Context, tf: str) -> pd.Series:
    """ATR del marco `tf` llevado a M1 sin lookahead."""
    if pd.Timedelta(tf) == pd.Timedelta("1min"):
        return ctx.atr()
    return ctx.cached(("atr_tf", tf), lambda: ind.align_higher_tf(ind.atr(ind.resample_ohlc(ctx.bars, tf)), ctx.bars.index, tf))


def _emit(ctx: Context, cond: pd.Series, tf: str) -> np.ndarray:
    if pd.Timedelta(tf) == pd.Timedelta("1min"):
        return _arr(cond)
    return ind.align_higher_tf_events(cond, ctx.bars.index, tf)


@register("sweep", "setup",
          "Barrida con mecha: la vela perfora el mínimo (máximo) de las N velas previas y cierra de vuelta dentro "
          "→ entrada en contra de la barrida. Stop detrás de la mecha (+buffer), con mínimo min_stop_atr·ATR.",
          lookback=10, tf="1min", close_pos=0.5, buffer_atr=0.1, min_stop_atr=0.5)
def setup_sweep(ctx: Context, lookback: int, tf: str, close_pos: float, buffer_atr: float, min_stop_atr: float):
    b = ctx.bars if pd.Timedelta(tf) == pd.Timedelta("1min") else ind.resample_ohlc(ctx.bars, tf)
    a = ind.atr(b)
    prev_lo = b["low"].rolling(lookback).min().shift()
    prev_hi = b["high"].rolling(lookback).max().shift()
    rng = (b["high"] - b["low"]).replace(0, np.nan)
    pos = (b["close"] - b["low"]) / rng
    long_c = (b["low"] < prev_lo) & (b["close"] > prev_lo) & (pos >= close_pos)
    short_c = (b["high"] > prev_hi) & (b["close"] < prev_hi) & (pos <= 1 - close_pos)
    d_long = np.maximum(b["close"] - b["low"] + buffer_atr * a, min_stop_atr * a)
    d_short = np.maximum(b["high"] - b["close"] + buffer_atr * a, min_stop_atr * a)
    dist = d_long.where(long_c, d_short.where(short_c))
    if pd.Timedelta(tf) != pd.Timedelta("1min"):
        dist = ind.align_higher_tf(dist, ctx.bars.index, tf)
    return _emit(ctx, long_c, tf), _emit(ctx, short_c, tf), dist.to_numpy(float)


@register("orb", "setup",
          "Ruptura del rango de apertura: primer cierre M1 de la sesión por encima (debajo) del máximo (mínimo) de los "
          "primeros `minutes`. Stop = sl_atr·ATR(atr_tf).",
          minutes=15, sl_atr=1.0, atr_tf="5min")
def setup_orb(ctx: Context, minutes: int, sl_atr: float, atr_tf: str):
    sess = ctx.session()
    orng = ind.opening_range(ctx.bars, sess, minutes)
    c = ctx.bars["close"]
    key = sess["session_date"].to_numpy()
    up = (c > orng["or_high"]).fillna(False)
    dn = (c < orng["or_low"]).fillna(False)
    first_up = up & (up.astype(int).groupby(key).cumsum() == 1)
    first_dn = dn & (dn.astype(int).groupby(key).cumsum() == 1)
    stop = (_atr_tf(ctx, atr_tf) * sl_atr).to_numpy()
    return _arr(first_up), _arr(first_dn), stop


@register("sr_bounce", "setup",
          "Método de John: soporte/resistencia = último swing confirmado (fractal de k velas). Compra cuando una vela "
          "toca el soporte (a menos de tol·ATR) y cierra por encima con mecha inferior >= wick del rango; vende igual "
          "en la resistencia. Stop detrás del nivel (+buffer), con mínimo min_stop_atr·ATR.",
          k=5, tf="1min", tol_atr=0.25, wick=0.0, buffer_atr=0.25, min_stop_atr=0.5)
def setup_sr_bounce(ctx: Context, k: int, tf: str, tol_atr: float, wick: float, buffer_atr: float, min_stop_atr: float):
    b = ctx.bars if pd.Timedelta(tf) == pd.Timedelta("1min") else ind.resample_ohlc(ctx.bars, tf)
    a = ind.atr(b)
    sw = ind.swing_levels(b, k)
    sup, res = sw["swing_low"], sw["swing_high"]
    rng = (b["high"] - b["low"]).replace(0, np.nan)
    lower_w = (b[["open", "close"]].min(axis=1) - b["low"]) / rng
    upper_w = (b["high"] - b[["open", "close"]].max(axis=1)) / rng
    long_c = (b["low"] <= sup + tol_atr * a) & (b["close"] > sup) & (lower_w >= wick) & (b["close"] < res)
    short_c = (b["high"] >= res - tol_atr * a) & (b["close"] < res) & (upper_w >= wick) & (b["close"] > sup)
    # una sola entrada por nivel: solo la primera vela que lo toca
    long_c &= ~long_c.shift(fill_value=False) | (sup != sup.shift())
    short_c &= ~short_c.shift(fill_value=False) | (res != res.shift())
    d_long = np.maximum(b["close"] - (sup - buffer_atr * a), min_stop_atr * a)
    d_short = np.maximum((res + buffer_atr * a) - b["close"], min_stop_atr * a)
    dist = d_long.where(long_c, d_short.where(short_c))
    if pd.Timedelta(tf) != pd.Timedelta("1min"):
        dist = ind.align_higher_tf(dist, ctx.bars.index, tf)
    return _emit(ctx, long_c.fillna(False), tf), _emit(ctx, short_c.fillna(False), tf), dist.to_numpy(float)


# -------------------------------------------------------------------------- filtros
@register("trend_m5", "filter", "Tendencia M5: cierre M5 por encima/debajo de su EMA (sin lookahead).", ema=20)
def f_trend_m5(ctx: Context, ema: int) -> LongShort:
    m5 = ind.resample_ohlc(ctx.bars, "5min")
    diff = m5["close"] - ind.ema(m5["close"], ema)
    aligned = ind.align_higher_tf(diff, ctx.bars.index, "5min")
    return _arr(aligned > 0), _arr(aligned < 0)


@register("ema_9_20", "filter", "EMA 9 por encima (largos) / debajo (cortos) de EMA 20 en M1.", fast=9, slow=20)
def f_ema_cross(ctx: Context, fast: int, slow: int) -> LongShort:
    d = ctx.ema(fast) - ctx.ema(slow)
    return _arr(d > 0), _arr(d < 0)


@register("vwap", "filter", "Precio por encima (largos) / debajo (cortos) del VWAP anclado a la apertura.")
def f_vwap(ctx: Context) -> LongShort:
    vwap = ctx.cached("vwap", lambda: ind.anchored_vwap(ctx.bars, ctx.session()["session_date"]))
    c = ctx.bars["close"]
    return _arr(c > vwap), _arr(c < vwap)


@register("opening_range", "filter", "Solo largos sobre el máximo / cortos bajo el mínimo del Opening Range.", minutes=15)
def f_opening_range(ctx: Context, minutes: int) -> LongShort:
    orng = ind.opening_range(ctx.bars, ctx.session(), minutes)
    c = ctx.bars["close"]
    return _arr(c > orng["or_high"]), _arr(c < orng["or_low"])


@register("structure_break", "filter", "Ruptura de estructura: cierre más allá del último swing confirmado.", k=3)
def f_structure(ctx: Context, k: int) -> LongShort:
    sw = ind.swing_levels(ctx.bars, k)
    c = ctx.bars["close"]
    return _arr(c > sw["swing_high"]), _arr(c < sw["swing_low"])


@register("impulse", "filter", "Hubo una vela de impulso (cuerpo > k·ATR) a favor en las últimas N barras.", k=1.5, within=10)
def f_impulse(ctx: Context, k: float, within: int) -> LongShort:
    b = ctx.bars
    body = b["close"] - b["open"]
    a = ctx.atr()
    up = ind.bars_since(body > k * a) < within
    dn = ind.bars_since(body < -k * a) < within
    return _arr(up), _arr(dn)


@register("pullback", "filter", "Retroceso: el precio tocó la EMA lenta en las últimas N barras.", ema=20, within=5)
def f_pullback(ctx: Context, ema: int, within: int) -> LongShort:
    b = ctx.bars
    e = ctx.ema(ema)
    touched_long = ind.bars_since(b["low"] <= e) < within
    touched_short = ind.bars_since(b["high"] >= e) < within
    return _arr(touched_long), _arr(touched_short)


@register("rejection_candle", "filter", "Vela de rechazo: cierra en el tercio favorable de su rango.", close_pos=0.66)
def f_rejection(ctx: Context, close_pos: float) -> LongShort:
    b = ctx.bars
    rng = (b["high"] - b["low"]).replace(0, np.nan)
    pos = (b["close"] - b["low"]) / rng
    return _arr(pos >= close_pos), _arr(pos <= 1 - close_pos)


@register("wick_body_ratio", "filter", "Mecha contraria / cuerpo >= ratio (rechazo fuerte).", ratio=1.5)
def f_wick_body(ctx: Context, ratio: float) -> LongShort:
    b = ctx.bars
    body = (b["close"] - b["open"]).abs().clip(lower=1e-9)
    lower = b[["open", "close"]].min(axis=1) - b["low"]
    upper = b["high"] - b[["open", "close"]].max(axis=1)
    return _arr(lower / body >= ratio), _arr(upper / body >= ratio)


@register("volume", "filter", "Tick volume de la barra > mult × media de N barras.", mult=1.2, n=20)
def f_volume(ctx: Context, mult: float, n: int) -> LongShort:
    v = ctx.bars["tick_volume"]
    ok = _arr(v > mult * v.rolling(n).mean().shift())
    return ok, ok


@register("volatility", "filter", "ATR relativo (ATR / mediana de ATR de N barras) dentro de [lo, hi].", lo=0.8, hi=2.5, n=1000)
def f_volatility(ctx: Context, lo: float, hi: float, n: int) -> LongShort:
    a = ctx.atr()
    rel = a / a.rolling(n, min_periods=n // 4).median()
    ok = _arr((rel >= lo) & (rel <= hi))
    return ok, ok


@register("spread", "filter", "Spread <= max_atr × ATR (el coste no se come el movimiento).", max_atr=0.15)
def f_spread(ctx: Context, max_atr: float) -> LongShort:
    ok = _arr(ctx.bars["spread"] <= max_atr * ctx.atr())
    return ok, ok


@register("session_hours", "filter", "Solo opera entre start y end minutos desde la apertura de sesión.", start=0, end=120)
def f_session_hours(ctx: Context, start: int, end: int) -> LongShort:
    m = ctx.session()["minutes_from_open"]
    ok = _arr((m >= start) & (m < end))
    return ok, ok


@register("ema_side", "filter", "Largos solo con el cierre por encima de la EMA; cortos solo por debajo (la media de John).", ema=50)
def f_ema_side(ctx: Context, ema: int) -> LongShort:
    d = ctx.bars["close"] - ctx.ema(ema)
    return _arr(d > 0), _arr(d < 0)


@register("no_momentum_against", "filter",
          "Evita la trampa: no comprar si en las últimas N velas hubo k velas bajistas fuertes (cuerpo > body_atr·ATR); simétrico en ventas.",
          n=5, k=2, body_atr=0.8)
def f_no_momentum_against(ctx: Context, n: int, k: int, body_atr: float) -> LongShort:
    b = ctx.bars
    body = (b["close"] - b["open"]) / ctx.atr()
    strong_dn = (body < -body_atr).astype(int).rolling(n).sum()
    strong_up = (body > body_atr).astype(int).rolling(n).sum()
    return _arr(strong_dn < k), _arr(strong_up < k)


def _rsi(close: pd.Series, n: int) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


@register("rsi_zone", "filter", "RSI(14) en zona de giro: largos con RSI <= lo, cortos con RSI >= hi.", n=14, lo=40, hi=60)
def f_rsi_zone(ctx: Context, n: int, lo: float, hi: float) -> LongShort:
    r = _rsi(ctx.bars["close"], n)
    return _arr(r <= lo), _arr(r >= hi)


@register("ao_turn", "filter", "Awesome Oscillator girando a favor: largos si AO sube respecto a la vela anterior; cortos si baja.")
def f_ao_turn(ctx: Context) -> LongShort:
    b = ctx.bars
    mid = (b["high"] + b["low"]) / 2
    ao = mid.rolling(5).mean() - mid.rolling(34).mean()
    return _arr(ao > ao.shift()), _arr(ao < ao.shift())


# Pendientes (definir con John antes de implementar): "retest" (vuelta al nivel roto
# dentro de N barras con tolerancia en ATR) y "score" (suma ponderada de filtros >= umbral).


def resolve(name: str, params: dict | None = None) -> tuple[Component, dict]:
    comp = get(name)
    merged = {**comp.defaults, **(params or {})}
    unknown = set(merged) - set(comp.defaults)
    if unknown:
        raise ValueError(f"Parámetros desconocidos para '{name}': {sorted(unknown)}")
    return comp, merged
