from __future__ import annotations

from pathlib import Path
from versioning_tool.core import run_git

MERMAID_HEADER = "```mermaid\ngitGraph\n"


def recent_tag_chain(main_branch: str, max_tags: int) -> list[str]:
    # tags reachable from main, sorted by taggerdate descending
    tags = run_git(["tag", "--merged", main_branch, "--sort=-taggerdate"]).splitlines()
    return tags[:max_tags]


def _short_msg(msg: str, length: int = 32) -> str:
    """Return a commit message truncated to length."""
    clean = msg.strip().replace('"', "'")  # avoid breaking mermaid strings
    return (clean[:length] + "…") if len(clean) > length else clean


def graph_for_main(main_branch: str = "main", max_tags: int = 12) -> str:
    """Produce a mermaid gitGraph with SHA + short commit message, branches, merges, and tags."""

    log = run_git(
        [
            "log",
            "--all",
            "--decorate=short",
            "--pretty=format:%h|%d|%s|%p",
            "--topo-order",
            "--reverse",
        ]
    ).splitlines()

    lines = ["```mermaid", "gitGraph", '    commit id: "root"']

    branches = {main_branch: None}
    current_branch = main_branch

    for entry in log:
        sha, deco, msg, parents = entry.split("|", 3)
        deco = deco.strip(" ()")
        parents = parents.split() if parents else []

        # Commit id with SHA + 32-char truncated message
        commit_text = f"{sha} {_short_msg(msg)}"
        commit_line = f'    commit id: "{commit_text}"'

        # Tags
        tags = [d for d in deco.split(", ") if d.startswith("tag:")]
        for t in tags:
            commit_line += f' tag: "{t.replace("tag: ", "")}"'

        # Branch names (skip HEAD ->, strip origin/)
        branch_names = [
            d.replace("origin/", "")
            for d in deco.split(", ")
            if d and not d.startswith("tag:") and not d.startswith("HEAD ->")
        ]
        for b in branch_names:
            if b not in branches:
                lines.append(f"    branch {b}")
                branches[b] = sha
                current_branch = b

        # Merges
        if len(parents) > 1:
            for parent in parents[1:]:
                parent_branch = next((b for b, h in branches.items() if h == parent), None)
                if parent_branch:
                    commit_line = f"    merge {parent_branch}"

        lines.append(commit_line)
        branches[current_branch] = sha

    lines.append("```")
    return "\n".join(lines)


def write_graph_to_readme(readme: Path, heading: str, content: str):
    text = readme.read_text(encoding="utf-8") if readme.exists() else ""
    marker = f"\n## {heading}\n"
    start = text.find(marker)
    if start == -1:
        # append section
        new = text.rstrip() + marker + "\n" + content + "\n"
    else:
        # replace section from marker to next heading or EOF
        next_h = text.find("\n## ", start + 1)
        if next_h == -1:
            new = text[:start] + marker + "\n" + content + "\n"
        else:
            new = text[:start] + marker + "\n" + content + "\n" + text[next_h:]
    readme.write_text(new, encoding="utf-8")
