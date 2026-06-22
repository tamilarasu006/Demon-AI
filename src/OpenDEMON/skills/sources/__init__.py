"""Skill source resolvers — Hermes, OpenClaw, generic GitHub."""

from DEMON.skills.sources.base import ResolvedSkill, SourceResolver
from DEMON.skills.sources.github import GitHubResolver
from DEMON.skills.sources.hermes import HERMES_REPO_URL, HermesResolver
from DEMON.skills.sources.openclaw import OPENCLAW_REPO_URL, OpenClawResolver

__all__ = [
    "GitHubResolver",
    "HERMES_REPO_URL",
    "HermesResolver",
    "OPENCLAW_REPO_URL",
    "OpenClawResolver",
    "ResolvedSkill",
    "SourceResolver",
]
