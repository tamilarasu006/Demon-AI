"""Operators — persistent, scheduled autonomous agents."""

from OpenDEMON.operators.loader import load_operator
from OpenDEMON.operators.manager import OperatorManager
from OpenDEMON.operators.types import OperatorManifest

__all__ = ["OperatorManifest", "OperatorManager", "load_operator"]
