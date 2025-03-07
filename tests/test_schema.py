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


def test_schema_registry_tracks_current_version() -> None:
    from echoparley.schema import SchemaRegistry

    registry = SchemaRegistry()
    registry.register("session", SchemaVersion(1, 0))
    registry.register("session", SchemaVersion(1, 2))
    assert registry.supports("session", SchemaVersion(1, 0))
    assert registry.current("session") == SchemaVersion(1, 2)


def test_schema_registry_rejects_duplicates_and_unknown_kinds() -> None:
    from echoparley.schema import SchemaRegistry

    registry = SchemaRegistry()
    registry.register("session", SchemaVersion(1))
    with pytest.raises(ValueError, match="already registered"):
        registry.register("session", SchemaVersion(1))
    with pytest.raises(KeyError, match="unknown schema"):
        registry.current("missing")


def test_migration_chain_preserves_input_and_applies_order() -> None:
    from echoparley.schema import migrate_mapping

    source = {"events": 2}
    migrations = {
        (SchemaVersion(1, 0), SchemaVersion(1, 1)): lambda item: {**item, "seed": 0},
        (SchemaVersion(1, 1), SchemaVersion(1, 2)): lambda item: {**item, "events": 3},
    }
    result = migrate_mapping(source, SchemaVersion(1, 0), SchemaVersion(1, 2), migrations)
    assert result == {"events": 3, "seed": 0}
    assert source == {"events": 2}


def test_migration_chain_reports_missing_step() -> None:
    from echoparley.schema import migrate_mapping

    with pytest.raises(ValueError, match=r"missing migration 1\.0 -> 1\.1"):
        migrate_mapping({}, SchemaVersion(1, 0), SchemaVersion(1, 1), {})
