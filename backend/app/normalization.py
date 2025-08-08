import re
from typing import Set

# Normalized (lowercase, punctuation stripped) corporate suffixes.
# Extendable to support more variants in the future.
LEGAL_SUFFIXES: Set[str] = {
    "llc",
    "inc",
    "corp",
    "ltd",
    "pvt ltd",
    "plc",
    "sa",
    "ag",
    "gmbh",
    "co",
    "company",
    "llp",
    "limited",
}


def strip_legal_suffixes(name: str) -> str:
    """Remove known legal suffixes from the end of a company name.

    Comparison is case-insensitive and ignores punctuation within the suffix.
    """

    tokens = name.strip().split()
    while tokens:
        token_clean = re.sub(r"[^a-z]", "", tokens[-1].lower())
        if not token_clean:
            tokens.pop()
            continue
        # Handle two-word suffixes like "pvt ltd"
        if len(tokens) >= 2:
            two_token_clean = (
                re.sub(r"[^a-z]", "", tokens[-2].lower()) + " " + token_clean
            )
            if two_token_clean in LEGAL_SUFFIXES:
                tokens.pop()
                tokens.pop()
                continue
        if token_clean in LEGAL_SUFFIXES:
            tokens.pop()
            continue
        break
    return " ".join(tokens)


def normalize_company_name(name: str) -> str:
    """Normalize a company name by stripping common legal suffixes.

    The original casing and internal punctuation are preserved.
    """

    if not name:
        return ""
    cleaned = strip_legal_suffixes(name.strip())
    return cleaned
