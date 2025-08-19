import re
import datetime

from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

from versioning_tool.core import run_git, last_tag_on_branch

SECTION_RULES = [
    ("⚠️ Breaking Changes", [r"BREAKING CHANGE", r"^feat!:"]),
    ("✨ Features", [r"^feat:"]),
    ("🐛 Fixes", [r"^fix:"]),
    ("🧰 Other", [r".*"]),
]


def _clean_message(msg: str, repo_url: Optional[str] = None) -> str:
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
        # Handle PR references
        msg = re.sub(r"\(#(\d+)\)", rf"[#\1]({repo_url}/pull/\1)", msg)
        # Handle issue references
        msg = re.sub(r"#(\d+)(?!\])", rf"[#\1]({repo_url}/issues/\1)", msg)

    return msg


def _get_contributors(since_ref: str) -> List[str]:
    """Get list of contributors since last release"""
    try:
        contributors = run_git(
            ["log", f"{since_ref}..HEAD", "--pretty=format:%an", "--reverse"]
        ).splitlines()
        return sorted(set(contributors))
    except Exception:
        return []


def _group_messages(
    messages: List[str], group_order: Optional[List[str]] = None, repo_url: Optional[str] = None
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
        ordered = [(t, buckets.get(t, [])) for t in group_order if t in buckets and buckets[t]]
        # Add any remaining sections not in group_order
        for t in buckets:
            if t not in group_order and buckets[t]:
                ordered.append((t, buckets[t]))
        return ordered

    return [(t, items) for t, items in buckets.items() if items]


def _render(
    template_path: Path, header: str, entries: List[dict], repo_url: Optional[str] = None
) -> str:
    env = Environment(
        loader=FileSystemLoader(template_path.parent),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    tpl = env.get_template(template_path.name)
    return tpl.render(header=header, releases=entries, repo_url=repo_url)


def collect_since_last_tag_on_main(main_branch: str = "main") -> Tuple[List[str], str]:
    """Collect commit messages since last tag on main branch."""
    last = (
        last_tag_on_branch(main_branch)
        or run_git(["rev-list", "--max-parents=0", main_branch]).splitlines()[0]
    )
    msg = run_git(["log", f"{last}..{main_branch}", "--pretty=format:%s"])
    return [m for m in msg.splitlines() if m.strip()], last


def write_changelog(new_version: str, config: dict, repo_root: Path):
    """Write or update the changelog with new release information."""
    if not config.get("changelog", {}).get("main_only", True):
        return

    main_branch = config.get("default_branch", "main")
    messages, last_tag = collect_since_last_tag_on_main(main_branch)

    repo_url = config.get("repo_url")
    group_order = config.get("changelog", {}).get("group_order")
    grouped = _group_messages(messages, group_order, repo_url)

    # Get contributors since last release
    contributors = _get_contributors(last_tag)

    # Determine previous version for comparison links
    previous_version = (
        last_tag.replace("v", "") if last_tag and last_tag.startswith("v") else "initial"
    )

    entry = {
        "version": new_version,
        "previous_version": previous_version,
        "date": datetime.date.today().isoformat(),
        "sections": grouped,
        "contributors": contributors,
    }

    template_file = repo_root / config.get("changelog", {}).get("template", "CHANGELOG.md.j2")
    header = config.get("changelog", {}).get("header", "Changelog")

    changelog_path = repo_root / "CHANGELOG.md"
    new_text = _render(template_file, header, [entry], repo_url)

    # Merge with existing changelog
    prev_content = ""
    if changelog_path.exists():
        prev_content = changelog_path.read_text(encoding="utf-8")

        # Try to find where existing releases start to prepend new one
        first_release_pos = prev_content.find("## [")
        if first_release_pos != -1:
            # Insert new release before existing ones
            merged = (
                prev_content[:first_release_pos].rstrip()
                + "\n\n"
                + new_text.rstrip()
                + "\n\n"
                + prev_content[first_release_pos:].rstrip()
                + "\n"
            )
        else:
            # Append to beginning if no existing releases found
            merged = new_text.rstrip() + "\n\n" + prev_content.rstrip() + "\n"
    else:
        merged = new_text.rstrip() + "\n"

    changelog_path.write_text(merged, encoding="utf-8")


def generate_release_notes(new_version: str, config: dict, repo_root: Path) -> str:
    """Generate release notes for GitHub releases without modifying the changelog file."""
    main_branch = config.get("default_branch", "main")
    messages, last_tag = collect_since_last_tag_on_main(main_branch)

    repo_url = config.get("repo_url")
    group_order = config.get("changelog", {}).get("group_order")
    grouped = _group_messages(messages, group_order, repo_url)

    # Get contributors
    contributors = _get_contributors(last_tag)

    entry = {
        "version": new_version,
        "date": datetime.date.today().isoformat(),
        "sections": grouped,
        "contributors": contributors,
    }

    # Simple template for release notes
    release_notes = f"# Release {new_version}\n\n"
    release_notes += f"**Date**: {datetime.date.today().isoformat()}\n\n"

    for title, items in grouped:
        release_notes += f"## {title}\n\n"
        for item in items:
            release_notes += f"- {item}\n"
        release_notes += "\n"

    if contributors:
        release_notes += "## Contributors\n\n"
        for contributor in contributors:
            release_notes += f"- {contributor}\n"

    return release_notes


def get_unreleased_changes(main_branch: str = "main") -> List[str]:
    """Get commit messages that haven't been released yet."""
    messages, _ = collect_since_last_tag_on_main(main_branch)
    return messages
