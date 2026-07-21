"""Skill name validation helpers for CLI and API callers."""

from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from OpenDEMON.skills.manager import SkillManager


class UnknownSkillsError(ValueError):
    """Raised when one or more skill names cannot be resolved.

    Attributes
    ----------
    unknown_names : list[str]
        All names that were not found in the Skill_Catalog.
    catalog_empty : bool
        True when no skills are installed at all (affects error message).
    """

    def __init__(
        self,
        unknown_names: List[str],
        *,
        catalog_empty: bool = False,
    ) -> None:
        self.unknown_names = list(unknown_names)
        self.catalog_empty = catalog_empty
        super().__init__(str(self))

    def __str__(self) -> str:
        lines = [
            f"Unknown skill: '{n}'. Run 'DEMON skill list' to see installed skills."
            for n in self.unknown_names
        ]
        if self.catalog_empty:
            lines.append(
                "No skills are installed. Run 'DEMON skill install' to add skills."
            )
        return "\n".join(lines)


def resolve_skill_names(
    names: List[str],
    skill_manager: "SkillManager",
    *,
    catalog_is_empty: bool = False,
) -> List[str]:
    """Validate a list of skill names against the Skill_Catalog.

    Deduplicates *names* preserving insertion order, then checks every
    unique name against the catalog.  All unknown names are collected
    before raising so the caller sees the full error set at once.

    Parameters
    ----------
    names:
        Skill names to validate.  Duplicates are removed; order is preserved.
    skill_manager:
        The :class:`SkillManager` instance whose catalog is the source of truth.
    catalog_is_empty:
        Pass ``True`` when the catalog has zero entries so the error message
        includes a ``DEMON skill install`` hint.

    Returns
    -------
    list[str]
        Deduplicated, validated skill names.

    Raises
    ------
    UnknownSkillsError
        If *any* name is not in the Skill_Catalog.  The exception carries
        **all** unknown names — not just the first one.
    """
    unique_names = list(dict.fromkeys(names))
    known = set(skill_manager.skill_names())
    unknown = [n for n in unique_names if n not in known]
    if unknown:
        raise UnknownSkillsError(unknown, catalog_empty=catalog_is_empty)
    return unique_names


__all__ = ["UnknownSkillsError", "resolve_skill_names"]
