"""External-framework subprocess backends (Hermes Agent, OpenClaw)."""

from DEMON.evals.backends.external.hermes_agent import HermesBackend
from DEMON.evals.backends.external.openclaw import OpenClawBackend

__all__ = ["HermesBackend", "OpenClawBackend"]
