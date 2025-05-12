"""Subword training, roundtrip, and vocabulary discipline tests."""

from __future__ import annotations

from echoparley import text


def test_text_normalization_is_idempotent() -> None:
    original = "  \uff28ello\tWORLD \n 港大  "
    normalized = text.normalize_text(original)
    assert normalized == "hello world 港大"
    assert text.normalize_text(normalized) == normalized
    assert text.normalize_text("MiXeD", lowercase=False) == "MiXeD"


def test_bpe_training_uses_lexical_tie_breaks() -> None:
    model = text.train_bpe(["ab ac", "ab"], 3)
    assert model.merges == (("a", "b"), ("ab", "</w>"), ("a", "c"))
    assert text.train_bpe(["ab ac", "ab"], 3) == model


def test_empty_bpe_corpus_has_no_merges() -> None:
    assert text.train_bpe([], 4).merges == ()


def test_subword_encoding_applies_merges_in_training_order() -> None:
    model = text.BPEModel((("h", "i"), ("hi", "</w>")))
    assert text.encode_subwords(model, "Hi h") == ("hi</w>", "h", "</w>")
    assert text.encode_subwords(model, "   ") == ()
