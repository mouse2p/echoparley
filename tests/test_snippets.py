from echoparley.snippets import PythonSnippet, extract_python_snippets


def test_extract_marked_python_snippets_with_line_numbers() -> None:
    markdown = "before\n```python echoparley-run\nx = 1\n```\nafter\n"
    assert extract_python_snippets(markdown) == (PythonSnippet("x = 1\n", 3),)
