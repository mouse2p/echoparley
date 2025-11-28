import pytest

from echoparley.proptest import CaseSet


def test_case_set_retains_seed_and_values() -> None:
    assert CaseSet(4, ("a", "b")).seed == 4
    with pytest.raises(ValueError, match="seed"):
        CaseSet(-1, (1,))


def test_stream_generator_is_seeded_and_schema_valid() -> None:
    from echoparley.proptest import generate_streams

    first = generate_streams(7, 5)
    assert first == generate_streams(7, 5)
    assert all(stream.policy == "time-aligned" for stream in first.values)
