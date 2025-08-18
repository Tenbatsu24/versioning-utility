import re
import datetime
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple
from jinja2 import Environment, FileSystemLoader, select_autoescape

from versioning_tool.core import run_git, last_tag_on_branch


SECTION_RULES = [
    ("⚠️ Breaking Changes", [r"BREAKING CHANGE", r"^feat!:"]),
    ("✨ Features", [r"^feat:"]),
    ("🐛 Fixes", [r"^fix:"]),
    ("🧰 Other", [r".*"]),
]


def _clean_message(msg: str, repo_url: str | None = None) -> str:
    """Normalize commit messages for changelog readability."""
    original = msg.strip()

    # Strip conventional prefixes
    msg = re.sub(
        r"^(feat|fix|add|remove|change|chore|refactor|docs|test|ci|style)!?:\s*", "", original
    )

    # Capitalize first letter
    msg = msg[:1].upper() + msg[1:] if msg else original

    # Link PR/issue references (#123)
    if repo_url:
        msg = re.sub(r"\(#(\d+)\)", rf"[#\1]({repo_url}/pull/\1)", msg)

    return msg


def _group_messages(
    messages: List[str], group_order: List[str] | None = None, repo_url: str | None = None
) -> List[Tuple[str, List[str]]]:
    """Group commit messages by type."""
    compiled = [(title, [re.compile(p) for p in pats]) for title, pats in SECTION_RULES]
    buckets: Dict[str, List[str]] = defaultdict(list)

    for m in messages:
        clean = _clean_message(m, repo_url)
        for title, regexes in compiled:
            if any(r.search(m) for r in regexes):
                buckets[title].append(clean)
                break

    # Deduplicate but show counts
    for t in buckets:
        counts = Counter(buckets[t])
        buckets[t] = [f"{msg} (x{n})" if n > 1 else msg for msg, n in counts.items()]

    if group_order:
        ordered = [(t, buckets.get(t, [])) for t in group_order if buckets.get(t)]
        for t in buckets:
            if t not in group_order:
                ordered.append((t, buckets[t]))
        return ordered
    return [(t, items) for t, items in buckets.items() if items]


def _render(template_path: Path, header: str, entries: List[dict]) -> str:
    env = Environment(loader=FileSystemLoader(template_path.parent), autoescape=select_autoescape())
    tpl = env.get_template(template_path.name)
    return tpl.render(header=header, releases=entries)


def collect_since_last_tag_on_main(main_branch: str = "main") -> Tuple[List[str], str]:
    last = (
        last_tag_on_branch(main_branch)
        or run_git(["rev-list", "--max-parents=0", main_branch]).splitlines()[0]
    )
    msg = run_git(["log", f"{last}..{main_branch}", "--pretty=format:%s"])
    return [m for m in msg.splitlines() if m.strip()], last


def write_changelog(new_version: str, config: dict, repo_root: Path):
    if not config.get("changelog", {}).get("main_only", True):
        return

    main_branch = config.get("default_branch", "main")
    messages, _ = collect_since_last_tag_on_main(main_branch)

    repo_url = config.get("repo_url")
    grouped = _group_messages(messages, config.get("changelog", {}).get("group_order"), repo_url)

    version_link = (
        f"[{new_version}]({repo_url}/releases/tag/{new_version})" if repo_url else new_version
    )
    entry = {
        "version": version_link,
        "date": datetime.date.today().isoformat(),
        "sections": grouped,
    }

    template_file = repo_root / config.get("changelog", {}).get("template", "CHANGELOG.md.j2")
    header = config.get("changelog", {}).get("header", "Changelog")

    changelog_path = repo_root / "CHANGELOG.md"
    new_text = _render(template_file, header, [entry])

    prev = ""
    if changelog_path.exists():
        prev = changelog_path.read_text(encoding="utf-8")

    merged = f"{new_text.rstrip()}\n\n{prev}".rstrip() + "\n"
    changelog_path.write_text(merged, encoding="utf-8")
