"""Canonical golfer names shared by data imports and maintenance tools."""

ALIASES = {
    "Grant": "Grant Flynn",
    "Jeremy": "Jeremy Flynn",
    "Leo": "Leo Berhost",
    "Ralph": "Ralph Reis",
    "Tim Stefl": "Tim Steffl",
}


def canonical_name(name: str) -> str:
    return ALIASES.get(name.strip(), name.strip())
