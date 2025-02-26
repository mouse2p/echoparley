"""Canonical, checksummed representations for offline artifacts."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


def canonical_json(value: object) -> str:
    """Encode JSON with stable ordering and no non-standard numeric values."""
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def content_checksum(value: object) -> str:
    """Return a SHA-256 checksum over canonical UTF-8 JSON."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ArtifactEnvelope:
    """A versioned payload with a checksum covering its semantic identity."""

    kind: str
    schema_version: str
    payload: dict[str, Any]
    checksum: str

    @classmethod
    def create(
        cls, kind: str, payload: dict[str, Any], schema_version: str = "1.0"
    ) -> ArtifactEnvelope:
        if not kind or any(character.isspace() for character in kind):
            raise ValueError("artifact kind must be a nonempty token")
        identity = {"kind": kind, "payload": payload, "schema_version": schema_version}
        return cls(kind, schema_version, payload, content_checksum(identity))

    def verify(self) -> None:
        """Raise when payload metadata no longer matches its checksum."""
        expected = type(self).create(self.kind, self.payload, self.schema_version).checksum
        if self.checksum != expected:
            raise ValueError("artifact checksum mismatch")

    def to_mapping(self) -> dict[str, Any]:
        self.verify()
        return {
            "checksum": self.checksum,
            "kind": self.kind,
            "payload": self.payload,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> ArtifactEnvelope:
        required = {"checksum", "kind", "payload", "schema_version"}
        if value.keys() != required:
            raise ValueError("artifact envelope fields do not match schema")
        envelope = cls(
            kind=str(value["kind"]),
            schema_version=str(value["schema_version"]),
            payload=dict(value["payload"]),
            checksum=str(value["checksum"]),
        )
        envelope.verify()
        return envelope


def encode_jsonl(envelopes: Iterable[ArtifactEnvelope]) -> bytes:
    """Encode envelopes as newline-terminated canonical JSONL."""
    lines = [canonical_json(envelope.to_mapping()) for envelope in envelopes]
    return (("\n".join(lines) + "\n") if lines else "").encode("utf-8")


def decode_jsonl(data: bytes) -> list[ArtifactEnvelope]:
    """Decode and verify canonical JSONL bytes."""
    if data and not data.endswith(b"\n"):
        raise ValueError("JSONL artifact must end with a newline")
    envelopes: list[ArtifactEnvelope] = []
    for line_number, raw_line in enumerate(data.splitlines(), 1):
        if not raw_line:
            raise ValueError(f"blank JSONL line at {line_number}")
        try:
            value = json.loads(raw_line)
            envelopes.append(ArtifactEnvelope.from_mapping(value))
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError(f"invalid JSONL artifact at line {line_number}: {error}") from error
    return envelopes
