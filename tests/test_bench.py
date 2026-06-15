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


def test_regression_guard_rejects_mismatched_cases() -> None:
    from echoparley.bench import BenchmarkSummary, RegressionGuard

    with pytest.raises(ValueError, match="does not match"):
        RegressionGuard("units", 10).assert_summary(BenchmarkSummary("stream", 1, 1, 1, 1, 0))
    with pytest.raises(ValueError, match="positive"):
        RegressionGuard("units", 0)


def test_benchmark_jsonl_roundtrips_exact_samples() -> None:
    from echoparley.bench import decode_benchmark_jsonl, encode_benchmark_jsonl

    samples = (BenchmarkSample("units", 0, 1.25, 0.1),)
    encoded = encode_benchmark_jsonl(samples)
    assert decode_benchmark_jsonl(encoded) == samples
    assert encoded.endswith(b"\n")


def test_benchmark_jsonl_rejects_unrelated_artifacts() -> None:
    from echoparley.artifacts import ArtifactEnvelope, encode_jsonl
    from echoparley.bench import decode_benchmark_jsonl

    data = encode_jsonl((ArtifactEnvelope.create("other", {}),))
    with pytest.raises(ValueError, match="unsupported"):
        decode_benchmark_jsonl(data)


def test_unit_benchmark_reports_rtf_samples() -> None:
    from echoparley.bench import benchmark_units

    samples = benchmark_units(3, 2)
    assert len(samples) == 2
    assert all(
        sample.case == "unit-extraction" and sample.real_time_factor is not None
        for sample in samples
    )


def test_stream_benchmark_reports_requested_repeats() -> None:
    from echoparley.bench import benchmark_streams

    assert [sample.repeat for sample in benchmark_streams(2, 2)] == [0, 1]


def test_simulator_benchmark_uses_synthetic_duration() -> None:
    from echoparley.bench import benchmark_simulator

    sample = benchmark_simulator(4, 1)[0]
    assert sample.case == "simulator"
    assert sample.work_seconds == 1.5 and sample.real_time_factor is not None


def test_representative_benchmarks_stay_below_loose_bounds() -> None:
    from echoparley.bench import (
        RegressionGuard,
        benchmark_simulator,
        benchmark_streams,
        benchmark_units,
        summarize_samples,
    )

    for samples in (benchmark_units(1, 1), benchmark_streams(1, 1), benchmark_simulator(1, 1)):
        RegressionGuard(samples[0].case, 10_000).assert_summary(summarize_samples(samples))


def test_benchmark_suite_groups_three_stable_cases() -> None:
    from echoparley.bench import benchmark_suite, benchmark_summaries

    summaries = benchmark_summaries(benchmark_suite(0, 1))
    assert [item.case for item in summaries] == ["unit-extraction", "stream-roundtrip", "simulator"]
    assert all(item.repeats == 1 for item in summaries)


def test_benchmark_environment_reports_runtime_versions() -> None:
    from echoparley.bench import benchmark_environment

    environment = benchmark_environment()
    assert environment.python and environment.numpy and environment.platform
    assert environment.package.count(".") == 2


def test_benchmark_environment_labels_unknown_platform(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import echoparley.bench

    monkeypatch.setattr(echoparley.bench.platform, "system", lambda: "")
    assert echoparley.bench.benchmark_environment().platform == "unknown"


def test_benchmark_metadata_labels_machine_dependence() -> None:
    from echoparley.bench import benchmark_run_metadata

    metadata = benchmark_run_metadata(4, 3)
    assert metadata["seed"] == 4 and metadata["machine_dependent"] is True


def test_benchmark_throughput_matches_hand_calculation() -> None:
    from echoparley.bench import BenchmarkSummary, ThroughputSummary, benchmark_throughput

    summary = BenchmarkSummary("stream", 3, 50, 50, 50, 0)
    assert benchmark_throughput(summary, 10) == ThroughputSummary("stream", 10, 200.0)


def test_benchmark_throughput_rejects_zero_work_or_time() -> None:
    from echoparley.bench import BenchmarkSummary, benchmark_throughput

    with pytest.raises(ValueError, match="positive"):
        benchmark_throughput(BenchmarkSummary("x", 1, 1, 1, 1, 0), 0)
    with pytest.raises(ValueError, match="positive"):
        benchmark_throughput(BenchmarkSummary("x", 1, 0, 0, 0, 0), 1)


def test_benchmark_baseline_requires_loose_positive_ratio() -> None:
    from echoparley.bench import BenchmarkBaseline

    assert BenchmarkBaseline("units", 10).tolerance_ratio == 10
    with pytest.raises(ValueError, match="invalid"):
        BenchmarkBaseline("units", 10, 0.5)


def test_baseline_comparison_uses_loose_ratio() -> None:
    from echoparley.bench import BenchmarkBaseline, BenchmarkSummary, compare_benchmark_baseline

    summary = BenchmarkSummary("units", 1, 25, 25, 25, 0)
    result = compare_benchmark_baseline(summary, BenchmarkBaseline("units", 10, 3))
    assert result.ratio == 2.5 and result.within_tolerance


def test_baseline_comparison_rejects_mismatched_case() -> None:
    from echoparley.bench import BenchmarkBaseline, BenchmarkSummary, compare_benchmark_baseline

    with pytest.raises(ValueError, match="does not match"):
        compare_benchmark_baseline(BenchmarkSummary("a", 1, 1, 1, 1, 0), BenchmarkBaseline("b", 1))


def test_benchmark_result_record_contains_computed_summaries() -> None:
    from echoparley.bench import BenchmarkSample, benchmark_result_record

    record = benchmark_result_record((BenchmarkSample("x", 0, 2),), seed=1, repeats=1)
    assert record["samples"] == 1
    assert record["summaries"][0]["mean_ms"] == 2


def test_benchmark_summary_artifacts_roundtrip() -> None:
    from echoparley.bench import (
        BenchmarkSummary,
        decode_benchmark_summaries,
        encode_benchmark_summaries,
    )

    summaries = (BenchmarkSummary("x", 2, 1.5, 1.5, 2, 0.7),)
    assert decode_benchmark_summaries(encode_benchmark_summaries(summaries)) == summaries
