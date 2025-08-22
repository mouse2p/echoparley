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
