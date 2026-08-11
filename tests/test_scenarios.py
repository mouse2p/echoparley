from echoparley.scenarios import BackchannelKind, classify_planted_backchannel, tutorial_scenario


def test_tutorial_scenario_plants_reproducible_topic_turns() -> None:
    scenario = tutorial_scenario(4)
    assert scenario == tutorial_scenario(4)
    assert scenario.name == "tutorial"
    assert {turn.topic for turn in scenario.turns} == {"loops"}
    assert [turn.speaker for turn in scenario.turns] == ["learner", "tutor", "learner", "tutor"]


def test_backchannel_taxonomy_is_explicit_not_inferred() -> None:
    assert classify_planted_backchannel(" MHM ") is BackchannelKind.CONTINUER
    assert classify_planted_backchannel("what") is BackchannelKind.REPAIR


def test_floor_contention_policies_have_stable_ties() -> None:
    from echoparley.scenarios import FloorContentionPolicy, resolve_floor_contention

    claims = (("a", 20), ("b", 30), ("c", 30))
    assert resolve_floor_contention(claims, FloorContentionPolicy.EARLIEST) == "a"
    assert resolve_floor_contention(claims, FloorContentionPolicy.ROUND_ROBIN, turn_index=4) == "b"
    assert resolve_floor_contention(claims, FloorContentionPolicy.LONGEST_WAIT) == "c"


def test_negotiation_scenario_contains_a_contested_floor() -> None:
    from echoparley.scenarios import negotiation_scenario

    scenario = negotiation_scenario(2)
    assert scenario.turns[0].text == "offer 50"
    assert len(scenario.overlaps()) == 1
    assert scenario.turns[2].kind == "interrupt"


def test_expanded_scenarios_vary_content_without_moving_boundaries() -> None:
    from echoparley.scenarios import negotiation_scenario

    tutorials = [tutorial_scenario(seed) for seed in range(3)]
    assert len({scenario.turns[0].text for scenario in tutorials}) == 3
    assert (
        len(
            {
                tuple((turn.start_ms, turn.end_ms) for turn in scenario.turns)
                for scenario in tutorials
            }
        )
        == 1
    )
    negotiations = [negotiation_scenario(seed) for seed in range(4)]
    assert len({scenario.turns[0].text for scenario in negotiations}) == 4


def test_expanded_scenario_catalog_reports_stable_choices() -> None:
    import pytest

    from echoparley.scenarios import make_expanded_scenario

    assert make_expanded_scenario("tutorial", 2).name == "tutorial"
    with pytest.raises(ValueError, match="negotiation, tutorial"):
        make_expanded_scenario("missing")


def test_noisy_channel_scenario_exposes_planted_mishearing() -> None:
    from echoparley.scenarios import noisy_channel_scenario

    fixture = noisy_channel_scenario(1)
    assert fixture.dialogue.name == "noisy-channel"
    assert fixture.mishearings[0].expected == "monday"
    assert fixture.mishearings[0].observed in fixture.dialogue.turns[1].text


def test_planted_mishearing_rejects_identical_forms() -> None:
    import pytest

    from echoparley.scenarios import PlantedMishearing

    with pytest.raises(ValueError, match="differ"):
        PlantedMishearing(0, "same", "same")


def test_topic_drift_scenario_plants_ordered_topic_changes() -> None:
    from echoparley.scenarios import topic_drift_scenario

    scenario = topic_drift_scenario(0)
    assert [turn.topic for turn in scenario.turns] == ["travel", "food", "music", "music"]
    assert scenario.overlaps() == ()


def test_casual_scenario_covers_backchannel_taxonomy() -> None:
    from echoparley.scenarios import casual_backchannel_scenario

    scenario = casual_backchannel_scenario(5)
    labels = {classify_planted_backchannel(turn.text) for turn in scenario.turns[1:]}
    assert labels == set(BackchannelKind)
    assert len(scenario.overlaps()) == 3


def test_scenario_topics_can_collapse_adjacent_repetitions() -> None:
    from echoparley.scenarios import scenario_topics, topic_drift_scenario

    scenario = topic_drift_scenario(0)
    assert scenario_topics(scenario) == ("travel", "food", "music")
    assert scenario_topics(scenario, collapse=False)[-2:] == ("music", "music")


def test_three_speaker_scenario_plants_contention() -> None:
    from echoparley.scenarios import three_speaker_scenario

    scenario = three_speaker_scenario(7)
    assert {turn.speaker for turn in scenario.turns} == {"a", "b", "c"}
    assert scenario.overlaps() == ((1, 2),)


def test_casual_annotations_key_each_planted_backchannel() -> None:
    from echoparley.scenarios import casual_backchannel_annotations, casual_backchannel_scenario

    annotations = casual_backchannel_annotations(casual_backchannel_scenario())
    assert [index for index, _ in annotations.backchannels] == [1, 2, 3]
    assert {kind for _, kind in annotations.backchannels} == set(BackchannelKind)


def test_scenario_annotation_validation_rejects_wrong_turns() -> None:
    import pytest

    from echoparley.scenarios import ScenarioAnnotations, validate_scenario_annotations

    with pytest.raises(ValueError, match="reference"):
        validate_scenario_annotations(
            tutorial_scenario(), ScenarioAnnotations(((0, BackchannelKind.REPAIR),))
        )


def test_manifest_two_contains_speakers_and_taxonomy() -> None:
    from echoparley.scenarios import (
        casual_backchannel_annotations,
        casual_backchannel_scenario,
        scenario_manifest,
    )

    scenario = casual_backchannel_scenario()
    manifest = scenario_manifest(scenario, casual_backchannel_annotations(scenario))
    assert manifest["schema_version"] == "2.0"
    assert manifest["speakers"] == ["a", "b"]
    assert manifest["turns"][1]["backchannel_kind"] == "continuer"


def test_manifest_two_turn_fields_are_exhaustive() -> None:
    from echoparley.scenarios import scenario_manifest

    manifest = scenario_manifest(tutorial_scenario(1))
    assert set(manifest) == {"schema_version", "name", "seed", "speakers", "turns"}
    assert set(manifest["turns"][0]) == {
        "speaker",
        "start_ms",
        "end_ms",
        "text",
        "kind",
        "topic",
        "backchannel_kind",
    }


def test_manifest_one_migrates_without_losing_turn_content() -> None:
    from echoparley.scenarios import migrate_scenario_manifest

    legacy = {
        "schema_version": "1.0",
        "name": "old",
        "seed": 1,
        "turns": [
            {"speaker": "a", "start_ms": 0, "end_ms": 2, "text": "x", "kind": "turn", "topic": None}
        ],
    }
    migrated = migrate_scenario_manifest(legacy)
    assert migrated["turns"][0]["text"] == "x"
    assert migrated["turns"][0]["backchannel_kind"] is None


def test_manifest_migration_rejects_unknown_versions() -> None:
    import pytest

    from echoparley.scenarios import migrate_scenario_manifest

    with pytest.raises(ValueError, match="unsupported"):
        migrate_scenario_manifest({"schema_version": "3.0", "turns": []})


def test_manifest_two_roundtrips_dialogue_and_annotations() -> None:
    from echoparley.scenarios import (
        casual_backchannel_annotations,
        casual_backchannel_scenario,
        scenario_from_manifest,
        scenario_manifest,
    )

    scenario = casual_backchannel_scenario(3)
    annotations = casual_backchannel_annotations(scenario)
    assert scenario_from_manifest(scenario_manifest(scenario, annotations)) == (
        scenario,
        annotations,
    )


def test_manifest_reader_rejects_stale_speaker_index() -> None:
    import pytest

    from echoparley.scenarios import scenario_from_manifest, scenario_manifest

    manifest = scenario_manifest(tutorial_scenario())
    manifest["speakers"] = ["nobody"]
    with pytest.raises(ValueError, match="speaker index"):
        scenario_from_manifest(manifest)


def test_corpus_statistics_count_planted_events() -> None:
    from echoparley.scenarios import (
        CorpusStatistics,
        casual_backchannel_scenario,
        corpus_statistics,
        three_speaker_scenario,
    )

    assert corpus_statistics(
        (casual_backchannel_scenario(), three_speaker_scenario())
    ) == CorpusStatistics(2, 8, 3, 4, 3, 4400)


def test_corpus_report_checksum_is_reproducible() -> None:
    from echoparley.scenarios import corpus_report, three_speaker_scenario

    first = corpus_report((three_speaker_scenario(0),))
    assert first == corpus_report((three_speaker_scenario(0),))
    assert first["data_origin"] == "synthetic-planted"


def test_scenario_catalog_contains_every_expanded_template() -> None:
    from echoparley.scenarios import scenario_catalog

    assert set(scenario_catalog()) == {
        "tutorial",
        "negotiation",
        "noisy-channel",
        "topic-drift",
        "casual-backchannel",
        "three-speaker-contention",
    }


def test_long_topic_scenario_is_seeded_and_sparse() -> None:
    from echoparley.scenarios import long_topic_scenario

    scenario = long_topic_scenario(2, 20)
    assert scenario == long_topic_scenario(2, 20)
    assert 1 < sum(turn.topic == "target" for turn in scenario.turns) < 10


def test_scenario_manifest_envelope_covers_schema_two_payload() -> None:
    from echoparley.scenarios import scenario_manifest_envelope

    envelope = scenario_manifest_envelope(tutorial_scenario(4))
    assert envelope.kind == "dialogue-scenario"
    assert envelope.schema_version == "2.0"
    assert envelope.payload["seed"] == 4
    envelope.verify()


def test_scenario_corpus_encoding_is_canonical_and_nonempty() -> None:
    import pytest

    from echoparley.scenarios import encode_scenario_corpus

    records = ((tutorial_scenario(2), None),)
    first = encode_scenario_corpus(records)
    assert first == encode_scenario_corpus(records)
    assert first.endswith(b"\n")
    with pytest.raises(ValueError, match="empty"):
        encode_scenario_corpus(())


def test_scenario_corpus_decoder_roundtrips_and_rejects_other_kinds() -> None:
    import pytest

    from echoparley.artifacts import ArtifactEnvelope, encode_jsonl
    from echoparley.scenarios import decode_scenario_corpus, encode_scenario_corpus

    scenario = tutorial_scenario(3)
    assert decode_scenario_corpus(encode_scenario_corpus(((scenario, None),)))[0][0] == scenario
    unrelated = encode_jsonl((ArtifactEnvelope.create("other", {}),))
    with pytest.raises(ValueError, match="unsupported"):
        decode_scenario_corpus(unrelated)
    damaged = bytearray(encode_scenario_corpus(((scenario, None),)))
    damaged[-3] = ord("x")
    with pytest.raises(ValueError, match="invalid JSONL"):
        decode_scenario_corpus(bytes(damaged))


def test_scenario_corpus_requires_unique_names_when_encoding_and_decoding() -> None:
    import pytest

    from echoparley.artifacts import encode_jsonl
    from echoparley.scenarios import (
        decode_scenario_corpus,
        encode_scenario_corpus,
        scenario_manifest_envelope,
    )

    scenario = tutorial_scenario(0)
    with pytest.raises(ValueError, match="unique"):
        encode_scenario_corpus(((scenario, None), (scenario, None)))
    duplicate_bytes = encode_jsonl(
        (scenario_manifest_envelope(scenario), scenario_manifest_envelope(scenario))
    )
    with pytest.raises(ValueError, match="unique"):
        decode_scenario_corpus(duplicate_bytes)
