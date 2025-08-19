from __future__ import annotations

import re
import fnmatch

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from packaging.version import Version

BUMP_ORDER = ["patch", "minor", "major"]  # ascending


@dataclass
class BumpDecision:
    bump: Optional[str]  # patch/minor/major or None
    prerelease: Optional[str]
    reason: str


def branch_match(branch: str, patterns: Dict[str, dict]) -> Optional[Tuple[str, dict]]:
    for pat, cfg in patterns.items():
        if fnmatch.fnmatch(branch, pat):
            return pat, cfg or {}
    return None


def conventional_commit_bump(msgs: List[str], bump_cfg: dict) -> Optional[str]:
    """
    Returns highest bump suggested by commit messages.
    """
    matched = set()
    for level in ["major", "minor", "patch"]:
        rules: List[str] = bump_cfg.get(level, [])
        regexes = [re.compile(r) for r in rules]
        if any(any(r.search(m) for r in regexes) for m in msgs):
            matched.add(level)
    if not matched:
        return None
    # pick highest according to BUMP_ORDER
    highest = max(matched, key=lambda x: BUMP_ORDER.index(x))
    return highest


def decide_bump(
    branch: str, msgs: List[str], cfg: dict, current_version: str | None = None
) -> BumpDecision:
    # Branch-specific overrides (hotfix/* etc.)
    br = branch_match(branch, cfg.get("branch_types", {}))
    prerelease = None
    branch_forced_bump = None
    if br:
        _, br_cfg = br
        prerelease = br_cfg.get("prerelease")
        branch_forced_bump = br_cfg.get("bump")

    # Conventional commits
    conv = conventional_commit_bump(msgs, cfg.get("conventional_bump", {}))

    # If branch forces bump (e.g., hotfix/*), that wins for stable release scenario
    bump = branch_forced_bump or conv

    # If branch suggests prerelease (feature/* => alpha), we’ll output prerelease label
    return BumpDecision(
        bump=bump,
        prerelease=prerelease,
        reason=f"branch={branch_forced_bump}, conventional={conv}, prerelease={prerelease}",
    )


def next_version(current: str, decision: BumpDecision) -> str:
    v = Version(current)
    if decision.prerelease:
        label = decision.prerelease
        # if already on same prerelease channel -> increment number
        if v.pre and v.pre[0] == label:
            num = v.pre[1] + 1
            return f"{v.major}.{v.minor}.{v.micro}-{label}.{num}"
        # reset to .1 from baseline (same major/minor/patch)
        return f"{v.major}.{v.minor}.{v.micro}-{label}.1"

    # stable release path
    bump = decision.bump or "patch"
    if bump == "major":
        return f"{v.major + 1}.0.0"
    if bump == "minor":
        return f"{v.major}.{v.minor + 1}.0"
    if bump == "patch":
        return f"{v.major}.{v.minor}.{v.micro + 1}"

    return f"{v.major}.{v.minor}.{v.micro}"
