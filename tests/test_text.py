"""Subword training, roundtrip, and vocabulary discipline tests."""

from __future__ import annotations

from echoparley import text


def test_text_normalization_is_idempotent() -> None:
    original = "  \uff28ello\tWORLD \n 港大  "
    normalized = text.normalize_text(original)
    assert normalized == "hello world 港大"
    assert text.normalize_text(normalized) == normalized
    assert text.normalize_text("MiXeD", lowercase=False) == "MiXeD"
