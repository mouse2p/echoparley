"""Schema-version boundaries and canonical representations."""

from __future__ import annotations

import pytest

from echoparley.schema import SchemaVersion


def test_schema_version_roundtrip_and_ordering() -> None:
    versions = [SchemaVersion.parse(text) for text in ("2.0", "1.9", "1.0")]
    assert [str(version) for version in sorted(versions)] == ["1.0", "1.9", "2.0"]


@pytest.mark.parametrize("value", ["", "1", "1.2.3", "v1.0", "1.-1", "one.zero"])
def test_schema_version_rejects_noncanonical_text(value: str) -> None:
    with pytest.raises(ValueError, match="invalid schema version"):
        SchemaVersion.parse(value)


@pytest.mark.parametrize("major,minor", [(0, 0), (-1, 0), (1, -1)])
def test_schema_version_rejects_out_of_range_parts(major: int, minor: int) -> None:
    with pytest.raises(ValueError, match="major >= 1"):
        SchemaVersion(major, minor)
