import numpy as np
import pandas as pd
import pytest

from botscalping.engine import Costs, Exits, run_backtest


def make_bars(rows, spread=0.0):
    idx = pd.date_range("2025-01-02 14:30", periods=len(rows), freq="1min", tz="UTC")
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx)
    df["tick_volume"] = 100.0
    df["spread"] = spread
    return df


def one_signal(n, side=1):
    lo, sh = np.zeros(n, bool), np.zeros(n, bool)
    (lo if side == 1 else sh)[0] = True
    return lo, sh


def test_long_hits_target():
    bars = make_bars([(100, 100, 100, 100), (100, 101, 99.5, 100.5), (100.5, 102.5, 100.4, 102)])
    lo, sh = one_signal(3)
    t = run_backtest(bars, lo, sh, np.full(3, 1.0), Exits(rr=2, max_bars=10))
    assert t.iloc[0]["reason"] == "target"
    assert t.iloc[0]["r"] == pytest.approx(2.0)


def test_stop_and_target_same_bar_counts_as_stop():
    bars = make_bars([(100, 100, 100, 100), (100, 103, 98, 100)])
    lo, sh = one_signal(2)
    t = run_backtest(bars, lo, sh, np.full(2, 1.0), Exits(rr=2, max_bars=10))
    assert t.iloc[0]["reason"] == "stop"
    assert t.iloc[0]["r"] == pytest.approx(-1.0)


def test_spread_is_paid_on_long():
    bars = make_bars([(100, 100, 100, 100), (100, 100.2, 99.9, 100), (100, 100, 100, 100)], spread=0.1)
    lo, sh = one_signal(3)
    t = run_backtest(bars, lo, sh, np.full(3, 1.0), Exits(rr=2, max_bars=2))
    assert t.iloc[0]["reason"] == "time"
    assert t.iloc[0]["r"] == pytest.approx(-0.1)  # compra a 100.1 (ask), sale a 100 (bid)


def test_short_target_uses_ask():
    bars = make_bars([(100, 100, 100, 100), (100, 100, 97.95, 98)], spread=0.1)
    lo, sh = one_signal(2, side=-1)
    t = run_backtest(bars, lo, sh, np.full(2, 1.0), Exits(rr=2, max_bars=5))
    # vende a 100, objetivo 98: el ask mínimo es 97.95 + 0.1 = 98.05 > 98 -> no llega
    assert t.iloc[0]["reason"] == "time"


def test_one_position_at_a_time():
    bars = make_bars([(100, 100.1, 99.9, 100)] * 10)
    lo = np.ones(10, bool)
    t = run_backtest(bars, lo, np.zeros(10, bool), np.full(10, 1.0), Exits(rr=2, max_bars=3))
    assert (t["entry_time"].iloc[1:].to_numpy() > t["exit_time"].iloc[:-1].to_numpy()).all()


def test_commission_reduces_r():
    bars = make_bars([(100, 100, 100, 100), (100, 102.5, 99.5, 102)])
    lo, sh = one_signal(2)
    t = run_backtest(bars, lo, sh, np.full(2, 1.0), Exits(rr=2), Costs(commission=0.1))
    assert t.iloc[0]["r"] == pytest.approx(1.9)
