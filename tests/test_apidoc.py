from echoparley.apidoc import missing_docstrings, public_api_entries


def test_api_inventory_is_sorted_and_module_local() -> None:
    entries = public_api_entries("echoparley.completion")
    assert [entry.name for entry in entries] == sorted(entry.name for entry in entries)
    assert {entry.kind for entry in entries} == {"function"}


def test_documented_phase_two_module_is_complete() -> None:
    assert missing_docstrings("echoparley.completion") == ()


def test_api_entry_renderer_uses_docstring_summary() -> None:
    from echoparley.apidoc import APIEntry, render_api_entry

    entry = APIEntry("echoparley.example", "run", "function", "Run one example.")
    assert render_api_entry(entry) == "- `run` (function): Run one example."


def test_module_reference_contains_public_completion_functions() -> None:
    from echoparley.apidoc import render_module_reference

    rendered = render_module_reference("echoparley.completion")
    assert rendered.startswith("## `echoparley.completion`\n")
    assert "`bash_completion`" in rendered and "`zsh_completion`" in rendered


def test_module_reference_follows_inventory_order() -> None:
    from echoparley.apidoc import render_module_reference

    rendered = render_module_reference("echoparley.snippets")
    positions = [
        rendered.index(f"`{name}`")
        for name in ("PythonSnippet", "execute_snippets", "extract_python_snippets")
    ]
    assert positions == sorted(positions)


def test_multi_module_reference_has_one_section_each() -> None:
    from echoparley.apidoc import render_api_reference

    rendered = render_api_reference(("echoparley.completion", "echoparley.snippets"))
    assert rendered.count("## `echoparley.") == 2
    assert rendered.endswith("\n")


def test_api_reference_rejects_empty_and_duplicate_modules() -> None:
    import pytest

    from echoparley.apidoc import render_api_reference

    with pytest.raises(ValueError, match="distinct"):
        render_api_reference(())
    with pytest.raises(ValueError, match="distinct"):
        render_api_reference(("echoparley.snippets", "echoparley.snippets"))


def test_phase_two_reference_modules_have_complete_docstrings() -> None:
    from echoparley.apidoc import PHASE_TWO_API_MODULES

    assert all(missing_docstrings(module) == () for module in PHASE_TWO_API_MODULES)


def test_api_inventory_mapping_fields_are_exhaustive() -> None:
    from echoparley.apidoc import api_inventory_mapping

    mapping = api_inventory_mapping(("echoparley.snippets",))
    assert set(mapping) == {"schema_version", "modules"}
    assert set(mapping["modules"][0]) == {"name", "entries"}
    assert all(
        set(entry) == {"name", "kind", "summary"} for entry in mapping["modules"][0]["entries"]
    )


def test_api_inventory_mapping_requires_modules() -> None:
    import pytest

    from echoparley.apidoc import api_inventory_mapping

    with pytest.raises(ValueError, match="requires"):
        api_inventory_mapping(())


def test_api_generator_script_exposes_main() -> None:
    import runpy

    namespace = runpy.run_path("scripts/generate_api_reference.py")
    assert callable(namespace["main"])
