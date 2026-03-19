from echoparley.apidoc import missing_docstrings, public_api_entries


def test_api_inventory_is_sorted_and_module_local() -> None:
    entries = public_api_entries("echoparley.completion")
    assert [entry.name for entry in entries] == sorted(entry.name for entry in entries)
    assert {entry.kind for entry in entries} == {"function"}


def test_documented_phase_two_module_is_complete() -> None:
    assert missing_docstrings("echoparley.completion") == ()
