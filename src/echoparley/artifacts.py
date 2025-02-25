"""Canonical, checksummed representations for offline artifacts."""

from __future__ import annotations

import hashlib
import json


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
