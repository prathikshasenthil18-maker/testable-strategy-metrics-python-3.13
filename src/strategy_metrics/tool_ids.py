"""Stable ids for workbook primary-tool strings (filesystem-safe, case-preserving)."""

from __future__ import annotations

import re


def normalize_primary_tool_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.replace("\n", " ").strip())


def primary_tool_slug(name: str) -> str:
    """Base filesystem id (lowercase). Use ``assign_primary_tool_slugs`` when names collide."""
    s = normalize_primary_tool_name(name)
    s = s.replace(".", "_dot_")
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", s).strip("_").lower()
    return slug[:120] or "unknown"


def assign_primary_tool_slugs(names: list[str]) -> dict[str, str]:
    """Map each exact workbook primary string to a unique, case-safe file id."""
    ordered = sorted(set(names), key=str.lower)
    out: dict[str, str] = {}
    used: set[str] = set()
    for name in ordered:
        base = primary_tool_slug(name)
        slug = base
        if slug in used:
            tag = re.sub(r"[^a-zA-Z0-9_]+", "_", normalize_primary_tool_name(name)).strip("_")[:48]
            slug = f"{base}__{tag.lower()}"
        used.add(slug)
        out[name] = slug
    return out
