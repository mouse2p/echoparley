"""Subword training, roundtrip, and vocabulary discipline tests."""

from __future__ import annotations

import pytest

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


def test_subword_roundtrip_matches_normalized_text() -> None:
    model = text.train_bpe(["hello harbor", "hello hill"], 8)
    original = "  HELLO  hill "
    assert text.decode_subwords(
        model, text.encode_subwords(model, original)
    ) == text.normalize_text(original)


def test_subword_decoder_rejects_partial_word() -> None:
    with pytest.raises(ValueError, match="inside a word"):
        text.decode_subwords(text.BPEModel(()), ("h", "i"))


def test_vocabulary_reserves_turn_tokens_in_order() -> None:
    tokens = ("<unk>", *text.TURN_TOKENS, "hello")
    vocabulary = text.Vocabulary(tokens)
    assert vocabulary.token_id("<interrupt>") == 4
    assert vocabulary.token_id("missing") == 0
    assert vocabulary.token(7) == "hello"


def test_vocabulary_rejects_reserved_token_reordering() -> None:
    with pytest.raises(ValueError, match="reserved-token"):
        text.Vocabulary(("<unk>", "<turn_end>"))


def test_built_vocabulary_has_stable_namespaces() -> None:
    model = text.train_bpe(["ba ab"], 1)
    vocabulary = text.build_vocabulary(model, ["ba ab", "<turn_start>"], 3)
    assert vocabulary.tokens[:7] == ("<unk>", *text.TURN_TOKENS)
    assert vocabulary.tokens[-3:] == ("<unit:0>", "<unit:1>", "<unit:2>")
    assert len(vocabulary.tokens) == len(set(vocabulary.tokens))


def test_bpe_mapping_roundtrip_has_exact_schema() -> None:
    model = text.BPEModel((("a", "b"), ("ab", "</w>")))
    mapping = text.bpe_to_mapping(model)
    assert mapping == {
        "schema_version": "1.0",
        "end_of_word": "</w>",
        "merges": [["a", "b"], ["ab", "</w>"]],
    }
    assert text.bpe_from_mapping(mapping) == model
    with pytest.raises(ValueError, match="unsupported"):
        text.bpe_from_mapping({"schema_version": "2.0"})


def test_bpe_mapping_rejects_non_array_and_ragged_merges() -> None:
    import pytest

    from echoparley.text import bpe_from_mapping

    base = {"schema_version": "1.0", "end_of_word": "</w>"}
    with pytest.raises(TypeError, match="two-item"):
        bpe_from_mapping({**base, "merges": "ab"})
    with pytest.raises(TypeError, match="two-item"):
        bpe_from_mapping({**base, "merges": [["a"]]})
