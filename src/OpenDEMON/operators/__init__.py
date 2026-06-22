"""Operators — persistent, scheduled autonomous agents."""

from DEMON.operators.loader import load_operator
from DEMON.operators.manager import OperatorManager
from DEMON.operators.types import OperatorManifest

__all__ = ["OperatorManifest", "OperatorManager", "load_operator"]
