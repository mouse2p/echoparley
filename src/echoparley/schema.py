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
