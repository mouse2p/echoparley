from echoparley.bench import BenchmarkSample


def test_benchmark_sample_reports_real_time_factor() -> None:
    assert BenchmarkSample("units", 0, 50, 0.5).real_time_factor == 0.1
    assert BenchmarkSample("stream", 1, 2).real_time_factor is None
