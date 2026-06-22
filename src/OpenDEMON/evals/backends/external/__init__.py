"""External-framework subprocess backends (Hermes Agent, OpenClaw)."""

from OpenDEMON.evals.backends.external.hermes_agent import HermesBackend
from OpenDEMON.evals.backends.external.openclaw import OpenClawBackend

__all__ = ["HermesBackend", "OpenClawBackend"]
