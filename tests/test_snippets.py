import pytest

from echoparley.snippets import PythonSnippet, extract_python_snippets


def test_extract_marked_python_snippets_with_line_numbers() -> None:
    markdown = "before\n```python echoparley-run\nx = 1\n```\nafter\n"
    assert extract_python_snippets(markdown) == (PythonSnippet("x = 1\n", 3),)


def test_snippet_extractor_ignores_unmarked_fences_and_rejects_unterminated() -> None:
    assert extract_python_snippets("```python\npass\n```\n") == ()
    with pytest.raises(ValueError, match="unterminated"):
        extract_python_snippets("```python echoparley-run\npass\n")
