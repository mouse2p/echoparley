"""Offline-first mechanics for reproducible spoken-dialogue experiments."""

from echoparley._version import __version__
from echoparley.config import ExperimentConfig
from echoparley.schema import SchemaVersion

__all__ = ["ExperimentConfig", "SchemaVersion", "__version__"]
