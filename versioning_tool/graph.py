from __future__ import annotations

from pathlib import Path
from versioning_tool.core import run_git

MERMAID_HEADER = "```mermaid\ngitGraph\n"


def recent_tag_chain(main_branch: str, max_tags: int) -> list[str]:
    # tags reachable from main, sorted by taggerdate descending
    tags = run_git(["tag", "--merged", main_branch, "--sort=-taggerdate"]).splitlines()
    return tags[:max_tags]


def graph_for_main(main_branch: str = "main", max_tags: int = 12) -> str:
    # We’ll produce a linear graph of tags on main for simplicity and clarity
    commits = run_git(["rev-list", "--first-parent", f"{main_branch}"]).splitlines()
    tags = {t: run_git(["rev-list", "-n", "1", t]) for t in recent_tag_chain(main_branch, max_tags)}
    lines = [MERMAID_HEADER, 'commit id: "root"']

    for c in reversed(commits):  # oldest -> newest
        line = f'commit id: "{c[:7]}"'
        tag = next((t for t, sha in tags.items() if sha == c), None)
        if tag:
            line += f' tag: "{tag}"'
        lines.append(line)

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
