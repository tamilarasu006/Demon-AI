"""Skill source resolvers — Hermes, OpenClaw, generic GitHub."""

from OpenDEMON.skills.sources.base import ResolvedSkill, SourceResolver
from OpenDEMON.skills.sources.github import GitHubResolver
from OpenDEMON.skills.sources.hermes import HERMES_REPO_URL, HermesResolver
from OpenDEMON.skills.sources.openclaw import OPENCLAW_REPO_URL, OpenClawResolver

__all__ = [
    "GitHubResolver",
    "HERMES_REPO_URL",
    "HermesResolver",
    "OPENCLAW_REPO_URL",
    "OpenClawResolver",
    "ResolvedSkill",
    "SourceResolver",
]
