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


def test_integer_shrinker_rejects_negative_inputs() -> None:
    from echoparley.proptest import shrink_non_negative

    with pytest.raises(ValueError, match="non-negative"):
        shrink_non_negative(-1)


def test_sequence_shrinker_includes_empty_and_single_removals() -> None:
    from echoparley.proptest import shrink_sequence

    candidates = shrink_sequence((1, 2, 3))
    assert candidates[0] == ()
    assert (2, 3) in candidates and (1, 2) in candidates


def test_property_checker_reports_reproducible_minimum() -> None:
    from echoparley.proptest import check_cases, shrink_non_negative

    failure = check_cases(CaseSet(8, (2, 7, 10)), lambda value: value < 0, shrink_non_negative)
    assert failure is not None
    assert (failure.seed, failure.case_index, failure.original, failure.minimal) == (8, 0, 2, 0)


def test_generated_streams_roundtrip_exactly() -> None:
    from echoparley.proptest import check_cases, generate_streams, stream_roundtrip_invariant

    assert check_cases(generate_streams(11, 30), stream_roundtrip_invariant) is None


def test_generated_sessions_replay_byte_identically() -> None:
    from echoparley.proptest import check_cases, generate_sessions, session_roundtrip_invariant

    assert check_cases(generate_sessions(12, 25), session_roundtrip_invariant) is None


def test_generated_endpoints_preserve_duplex_legality() -> None:
    from echoparley.proptest import check_cases, generate_endpoint_traces, legal_duplex_invariant

    assert check_cases(generate_endpoint_traces(13, 40), legal_duplex_invariant) is None


def test_generated_contexts_respect_every_small_budget() -> None:
    from echoparley.proptest import context_budget_invariant, generate_turns

    for turns in generate_turns(14, 20).values:
        assert all(context_budget_invariant(turns, budget) for budget in range(20))


def test_sequence_shrinking_finds_minimal_nonmonotone_trace() -> None:
    from echoparley.proptest import check_cases, shrink_sequence

    def monotone(values: tuple[int, ...]) -> bool:
        return list(values) == sorted(values)

    failure = check_cases(CaseSet(21, ((0, 2, 1, 3),)), monotone, shrink_sequence)
    assert failure is not None
    assert not monotone(failure.minimal)
    assert len(failure.minimal) <= len(failure.original)


def test_endpoint_trace_shrinker_preserves_monotone_time() -> None:
    from echoparley.proptest import generate_endpoint_traces, shrink_endpoint_trace

    trace = generate_endpoint_traces(5, 1).values[0]
    for candidate in shrink_endpoint_trace(trace):
        assert [item.time_ms for item in candidate] == sorted(item.time_ms for item in candidate)
