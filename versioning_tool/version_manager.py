from __future__ import annotations

import io
import re
import sys
import yaml
import argparse
import subprocess

from pathlib import Path

from versioning_tool.config import PYPROJECT_FILE, VERSIONING_CONFIG, PROJ_ROOT
from versioning_tool.core import (
    GitRange,
    current_branch,
    changed_files,
    commit_messages,
    filter_files,
    filter_commits,
)
from versioning_tool.rules import decide_bump, next_version
from versioning_tool.changelog import write_changelog
from versioning_tool.graph import graph_for_main, write_graph_to_readme


def read_pyproject_version(path: Path) -> str:
    try:
        import tomllib
    except Exception:
        import tomli as tomllib  # type: ignore
    with path.open("rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]


def write_pyproject_version(path: Path, new: str):
    txt = path.read_text(encoding="utf-8")
    txt = re.sub(r'version\s*=\s*"[0-9A-Za-z.\-]+"', f'version = "{new}"', txt)
    path.write_text(txt, encoding="utf-8")


def main_version_from_remote(default_branch: str) -> str:
    res = subprocess.run(
        ["git", "show", f"origin/{default_branch}:pyproject.toml"],
        capture_output=True,
        text=True,
        check=True,
    )
    try:
        import tomllib
    except Exception:
        import tomli as tomllib  # type: ignore
    data = tomllib.load(io.BytesIO(res.stdout.encode()))
    return data.get("project", {}).get("version", "0.0.0")


def load_cfg(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}


def compute_decision(cfg: dict, base_branch: str, head: str) -> tuple[str, str, str]:
    """
    Returns (suggested_version, reason, detected_bump)
    """
    branch = current_branch()
    current_ver = read_pyproject_version(PYPROJECT_FILE)

    # Choose comparison base for change detection
    base = f"origin/{base_branch}"
    gr = GitRange(base=base, head=head)

    files = changed_files(gr)
    msgs = commit_messages(gr)

    # filters
    files_kept = filter_files(files, cfg.get("ignore", {}).get("files", []))
    msgs_kept = filter_commits(msgs, cfg.get("ignore", {}).get("commits", []))

    # If *only* ignored files changed, force no bump unless branch enforces prerelease
    if files_kept == [] and msgs_kept == []:
        decision = decide_bump(branch, [], cfg, current_version=current_ver)
        if not decision.prerelease and decision.bump is None:
            # No changes requiring bumps
            return current_ver, "only ignored changes", "none"
        else:
            suggested = next_version(current_ver, decision)
            return (
                suggested,
                decision.reason,
                decision.bump or ("prerelease" if decision.prerelease else "patch"),
            )

    decision = decide_bump(branch, msgs_kept, cfg, current_version=current_ver)
    suggested = next_version(current_ver, decision)
    return (
        suggested,
        decision.reason,
        decision.bump or ("prerelease" if decision.prerelease else "patch"),
    )


def cmd_check(args):
    cfg = load_cfg(VERSIONING_CONFIG)
    base = cfg.get("default_branch", "main")
    suggested, reason, bump = compute_decision(cfg, base, "HEAD")
    current_ver = read_pyproject_version(PYPROJECT_FILE)
    print(f"Branch: {current_branch()}")
    print(f"Current: {current_ver}")
    print(f"Suggested: {suggested}  ({bump})")
    print(f"Reason: {reason}")


def cmd_bump(args):
    cfg = load_cfg(VERSIONING_CONFIG)
    base = cfg.get("default_branch", "main")
    suggested, reason, bump = compute_decision(cfg, base, "HEAD")

    if not args.yes:
        print(f"About to bump to {suggested} ({bump})")
        resp = input("Proceed? [y/N]: ").strip().lower()
        if resp != "y":
            print("Aborted.")
            sys.exit(1)

    write_pyproject_version(PYPROJECT_FILE, suggested)
    print(f"Bumped version to {suggested}")

    # Only generate changelog and graph when on main (per your request)
    if current_branch() == base and cfg.get("changelog", {}).get("main_only", True):
        write_changelog(suggested, cfg, PROJ_ROOT)
        print("Changelog updated.")

        # gcfg = cfg.get("graph", {})
        # g = graph_for_main(base, gcfg.get("max_tags", 12))
        # write_graph_to_readme(
        #     PROJ_ROOT / gcfg.get("readme_file", "README.md"),
        #     gcfg.get("start_after_heading", "Release Graph"),
        #     g,
        # )
        print("README release graph updated.")


def cmd_changelog(args):
    cfg = load_cfg(VERSIONING_CONFIG)
    base = cfg.get("default_branch", "main")
    # Use current pyproject version to emit an entry (main only)
    ver = read_pyproject_version(PYPROJECT_FILE)
    if current_branch() != base:
        print("Changelog generation is main-only (per config). Skipped.")
        return
    write_changelog(ver, cfg, PROJ_ROOT)
    print("Changelog updated.")


def cmd_graph(args):
    cfg = load_cfg(VERSIONING_CONFIG)
    base = cfg.get("default_branch", "main")
    gcfg = cfg.get("graph", {})

    # Get graph type from args or config
    graph_type = getattr(args, "type", gcfg.get("type", "release"))

    g = graph_for_main(base, gcfg.get("max_tags", 12), graph_type)
    write_graph_to_readme(
        PROJ_ROOT / gcfg.get("readme_file", "README.md"),
        gcfg.get("start_after_heading", "Release Graph"),
        g,
    )
    print("README release graph updated.")


def main():
    p = argparse.ArgumentParser(
        prog="version-manager", description="Versioning and changelog manager"
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="Show suggested version bump and reason").set_defaults(
        func=cmd_check
    )

    b = sub.add_parser("bump", help="Apply suggested bump (writes pyproject.toml)")
    b.add_argument("-y", "--yes", action="store_true", help="Non-interactive")
    b.set_defaults(func=cmd_bump)

    sub.add_parser(
        "changelog", help="Regenerate changelog for current version on main"
    ).set_defaults(func=cmd_changelog)

    g = sub.add_parser("graph", help="Regenerate Mermaid gitGraph section in README")
    g.add_argument(
        "--type",
        choices=["release", "simple", "detailed"],
        default="release",
        help="Type of graph to generate",
    )
    g.set_defaults(func=cmd_graph)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
