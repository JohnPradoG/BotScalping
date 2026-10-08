import numpy as np

from botscalping import stats
from botscalping.data import synthetic_bars
from botscalping.experiment import Config, evaluate
from botscalping.data import InstrumentSpec
from botscalping.engine import Costs, Exits


def test_holm_is_monotone_and_bounded():
    adj = stats.holm([0.01, 0.04, 0.03, 0.5])
    assert adj[0] == 0.04 and all(0 <= p <= 1 for p in adj)


def test_permutation_detects_real_difference():
    rng = np.random.default_rng(0)
    good, bad = rng.normal(0.3, 1, 400), rng.normal(-0.3, 1, 400)
    assert stats.permutation_diff(good, bad, n_perm=2000)["p_value"] < 0.01
    assert stats.permutation_diff(bad, good, n_perm=2000)["p_value"] > 0.5


def test_pipeline_runs_and_finds_no_edge_on_random_walk():
    cfg = Config(
        name="t", spec=InstrumentSpec("T", 0.01), data_path=None, broker_tz="UTC", in_sample_until=None,
        setup="breakout", setup_params={}, exits=Exits(2.0, 30), costs=Costs(),
        filters=[("trend_m5", {}), ("vwap", {}), ("volume", {})], base_filters=[], min_trades=50, benchmark_random=True,
    )
    df = evaluate(synthetic_bars(20_000, seed=1), cfg, "ladder")
    assert list(df["variante"]) == ["benchmark aleatorio", "baseline", "+ trend_m5", "+ vwap", "+ volume"]
    # Sin ventaja real + spread: ninguna variante debería salir significativamente positiva.
    assert (df["p_gt_0"] > 0.01).all()
