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
