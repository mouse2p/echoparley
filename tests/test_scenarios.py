from echoparley.scenarios import tutorial_scenario


def test_tutorial_scenario_plants_reproducible_topic_turns() -> None:
    scenario = tutorial_scenario(4)
    assert scenario == tutorial_scenario(4)
    assert scenario.name == "tutorial"
    assert {turn.topic for turn in scenario.turns} == {"loops"}
    assert [turn.speaker for turn in scenario.turns] == ["learner", "tutor", "learner", "tutor"]
