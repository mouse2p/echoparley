from echoparley.scenarios import tutorial_scenario


def test_tutorial_scenario_plants_reproducible_topic_turns() -> None:
    scenario = tutorial_scenario(4)
    assert scenario == tutorial_scenario(4)
    assert scenario.name == "tutorial"
    assert {turn.topic for turn in scenario.turns} == {"loops"}
    assert [turn.speaker for turn in scenario.turns] == ["learner", "tutor", "learner", "tutor"]


def test_negotiation_scenario_contains_a_contested_floor() -> None:
    from echoparley.scenarios import negotiation_scenario

    scenario = negotiation_scenario(2)
    assert scenario.turns[0].text == "offer 50"
    assert len(scenario.overlaps()) == 1
    assert scenario.turns[2].kind == "interrupt"
