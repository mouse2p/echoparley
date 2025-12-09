import pytest

from echoparley.bench import BenchmarkSample


def test_benchmark_sample_reports_real_time_factor() -> None:
    assert BenchmarkSample("units", 0, 50, 0.5).real_time_factor == 0.1
    assert BenchmarkSample("stream", 1, 2).real_time_factor is None


def test_benchmark_sample_rejects_invalid_fields() -> None:
    with pytest.raises(ValueError, match="fields"):
        BenchmarkSample("", 0, 1)
    with pytest.raises(ValueError, match="fields"):
        BenchmarkSample("case", 0, -1)
    with pytest.raises(ValueError, match="positive"):
        BenchmarkSample("case", 0, 1, 0)


def test_benchmark_summary_has_hand_checked_statistics() -> None:
    from echoparley.bench import BenchmarkSummary, summarize_samples

    samples = tuple(BenchmarkSample("x", index, value) for index, value in enumerate((1, 2, 3)))
    assert summarize_samples(samples) == BenchmarkSummary("x", 3, 2.0, 2.0, 3, 1.0)


def test_benchmark_summary_rejects_empty_and_mixed_cases() -> None:
    from echoparley.bench import summarize_samples

    with pytest.raises(ValueError, match="one case"):
        summarize_samples(())
    with pytest.raises(ValueError, match="one case"):
        summarize_samples((BenchmarkSample("a", 0, 1), BenchmarkSample("b", 1, 2)))


def test_benchmark_runner_excludes_warmups_from_samples() -> None:
    from echoparley.bench import run_benchmark

    calls = []
    ticks = iter((0.0, 0.001, 0.010, 0.013))
    samples = run_benchmark(
        "x", lambda: calls.append(1), warmup=2, repeats=2, clock=lambda: next(ticks)
    )
    assert len(calls) == 4
    assert [sample.elapsed_ms for sample in samples] == [1.0, 3.0]


def test_benchmark_runner_rejects_nonpositive_repeats() -> None:
    from echoparley.bench import run_benchmark

    with pytest.raises(ValueError, match="configuration"):
        run_benchmark("x", lambda: None, repeats=0)
    with pytest.raises(ValueError, match="configuration"):
        run_benchmark("", lambda: None)


def test_regression_guard_uses_measured_mean() -> None:
    from echoparley.bench import BenchmarkSummary, RegressionGuard

    guard = RegressionGuard("units", 100)
    guard.assert_summary(BenchmarkSummary("units", 2, 99, 99, 99, 0))
    with pytest.raises(AssertionError, match="loose bound"):
        guard.assert_summary(BenchmarkSummary("units", 2, 101, 101, 101, 0))
