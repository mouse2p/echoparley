import itertools

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


def test_stream_generator_varies_cases_and_validates_count() -> None:
    from echoparley.proptest import generate_streams

    assert generate_streams(1, 3) != generate_streams(2, 3)
    with pytest.raises(ValueError, match="invalid"):
        generate_streams(0, 0)


def test_turn_generator_produces_chronological_histories() -> None:
    from echoparley.proptest import generate_turns

    for turns in generate_turns(9, 8).values:
        assert all(left.end_ms <= right.start_ms for left, right in itertools.pairwise(turns))


def test_session_generator_produces_contiguous_sequences() -> None:
    from echoparley.proptest import generate_sessions

    for events in generate_sessions(2, 7).values:
        assert [event.sequence for event in events] == list(range(len(events)))
        assert [event.time_ms for event in events] == sorted(event.time_ms for event in events)


def test_endpoint_generator_is_monotone_and_bounded() -> None:
    from echoparley.proptest import generate_endpoint_traces

    for events in generate_endpoint_traces(5, 6).values:
        assert [event.time_ms for event in events] == sorted(event.time_ms for event in events)
        assert all(0 <= event.posterior <= 1 for event in events)


def test_integer_shrinker_moves_toward_zero() -> None:
    from echoparley.proptest import shrink_non_negative

    assert shrink_non_negative(10) == (0, 1, 2, 5)
    assert shrink_non_negative(0) == ()
