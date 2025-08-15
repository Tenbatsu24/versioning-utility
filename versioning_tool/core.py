from __future__ import annotations

import re
import fnmatch
import subprocess

from pathlib import Path
from dataclasses import dataclass
from typing import Iterable, List, Optional


@dataclass
class GitRange:
    base: str
    head: str = "HEAD"


def run_git(args: List[str]) -> str:
    res = subprocess.run(["git", *args], capture_output=True, text=True, check=True)
    return res.stdout.strip()


def current_branch() -> str:
    return run_git(["rev-parse", "--abbrev-ref", "HEAD"])


def last_tag_on_branch(branch: str) -> Optional[str]:
    try:
        # most recent tag reachable from this branch
        return run_git(["describe", "--tags", "--abbrev=0", branch])
    except subprocess.CalledProcessError:
        return None


def changed_files(gr: GitRange) -> List[str]:
    out = run_git(["diff", "--name-only", f"{gr.base}..{gr.head}"])
    return [l for l in out.splitlines() if l.strip()]


def commit_messages(gr: GitRange) -> List[str]:
    out = run_git(["log", f"{gr.base}..{gr.head}", "--pretty=format:%s"])
    return [l for l in out.splitlines() if l.strip()]


def filter_files(paths: Iterable[str], patterns: Iterable[str]) -> List[str]:
    keep = []
    for p in paths:
        if any(fnmatch.fnmatch(p, pat) for pat in patterns):
            continue
        keep.append(p)
    return keep


def filter_commits(msgs: Iterable[str], regexes: Iterable[str]) -> List[str]:
    regs = [re.compile(r) for r in regexes]
    return [m for m in msgs if not any(r.search(m) for r in regs)]
