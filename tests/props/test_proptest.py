import pytest

from echoparley.proptest import CaseSet


def test_case_set_retains_seed_and_values() -> None:
    assert CaseSet(4, ("a", "b")).seed == 4
    with pytest.raises(ValueError, match="seed"):
        CaseSet(-1, (1,))
