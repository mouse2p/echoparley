"""Version identifiers shared by serialized echoparley artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from functools import total_ordering


@total_ordering
@dataclass(frozen=True, slots=True)
class SchemaVersion:
    """A small, strictly positive major/minor schema identifier."""

    major: int
    minor: int = 0

    def __post_init__(self) -> None:
        if self.major < 1 or self.minor < 0:
            raise ValueError("schema version requires major >= 1 and minor >= 0")

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}"

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SchemaVersion):
            return NotImplemented
        return (self.major, self.minor) < (other.major, other.minor)

    @classmethod
    def parse(cls, value: str) -> SchemaVersion:
        """Parse the canonical ``major.minor`` representation."""
        parts = value.split(".")
        if len(parts) != 2 or not all(part.isascii() and part.isdigit() for part in parts):
            raise ValueError(f"invalid schema version: {value!r}")
        return cls(*(int(part) for part in parts))


@dataclass(slots=True)
class SchemaRegistry:
    """Track supported versions per artifact kind without global state."""

    _versions: dict[str, set[SchemaVersion]]

    def __init__(self) -> None:
        self._versions = {}

    def register(self, kind: str, version: SchemaVersion) -> None:
        if not kind:
            raise ValueError("schema kind cannot be empty")
        versions = self._versions.setdefault(kind, set())
        if version in versions:
            raise ValueError(f"schema already registered: {kind}@{version}")
        versions.add(version)

    def supports(self, kind: str, version: SchemaVersion) -> bool:
        return version in self._versions.get(kind, set())

    def current(self, kind: str) -> SchemaVersion:
        try:
            return max(self._versions[kind])
        except (KeyError, ValueError) as error:
            raise KeyError(f"unknown schema kind: {kind}") from error


Migration = callable


def migrate_mapping(
    value: dict[str, object],
    source: SchemaVersion,
    target: SchemaVersion,
    migrations: dict[tuple[SchemaVersion, SchemaVersion], object],
) -> dict[str, object]:
    """Apply registered same-major minor migrations in order."""
    if source.major != target.major or source > target:
        raise ValueError("migration requires an ascending path within one major version")
    current = source
    result = dict(value)
    while current < target:
        following = SchemaVersion(current.major, current.minor + 1)
        operation = migrations.get((current, following))
        if not callable(operation):
            raise ValueError(f"missing migration {current} -> {following}")
        migrated = operation(dict(result))
        if not isinstance(migrated, dict):
            raise TypeError("migration must return an object")
        result = migrated
        current = following
    return result
