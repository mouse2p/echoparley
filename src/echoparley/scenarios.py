"""Expanded planted scenarios for the synthetic dialogue laboratory."""

from __future__ import annotations

from echoparley.synth import DialogueScenario, TurnAnnotation


def tutorial_scenario(seed: int = 0) -> DialogueScenario:
    """Build a tutorial exchange with a planted clarification and answer."""
    subjects = ("arrays", "loops", "functions")
    subject = subjects[seed % len(subjects)]
    return DialogueScenario(
        "tutorial",
        seed,
        (
            TurnAnnotation("learner", 0, 520, f"explain {subject}", topic=subject),
            TurnAnnotation("tutor", 720, 1_420, f"scripted lesson about {subject}", topic=subject),
            TurnAnnotation("learner", 1_640, 1_940, "show one step", topic=subject),
            TurnAnnotation("tutor", 2_130, 2_700, "scripted worked step", topic=subject),
        ),
    )


def negotiation_scenario(seed: int = 0) -> DialogueScenario:
    """Build a negotiation with a deliberately contested floor interval."""
    amount = 40 + 5 * (seed % 4)
    return DialogueScenario(
        "negotiation",
        seed,
        (
            TurnAnnotation("buyer", 0, 700, f"offer {amount}", topic="price"),
            TurnAnnotation(
                "seller", 880, 1_700, "that is below the scripted target", topic="price"
            ),
            TurnAnnotation("buyer", 1_300, 1_620, "let me finish", "interrupt", "price"),
            TurnAnnotation("seller", 1_900, 2_350, "counter offer", topic="price"),
        ),
    )


EXPANDED_SCENARIOS = {
    "negotiation": negotiation_scenario,
    "tutorial": tutorial_scenario,
}


def make_expanded_scenario(name: str, seed: int = 0) -> DialogueScenario:
    """Resolve an expanded planted scenario by its stable catalog name."""
    try:
        return EXPANDED_SCENARIOS[name](seed)
    except KeyError as error:
        choices = ", ".join(sorted(EXPANDED_SCENARIOS))
        raise ValueError(f"unknown expanded scenario {name!r}; choose from {choices}") from error
