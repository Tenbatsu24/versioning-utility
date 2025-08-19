from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Optional
from versioning_tool.core import run_git


def _short_msg(msg: str, length: int = 25) -> str:
    """Return a commit message truncated to length."""
    clean = msg.strip().replace('"', "'").replace("\n", " ")  # avoid breaking mermaid strings
    return (clean[:length] + "…") if len(clean) > length else clean


def _get_tag_commit_map(tags: List[str]) -> Dict[str, str]:
    """Get mapping of tags to their commit SHAs."""
    tag_commit_map = {}
    for tag in tags:
        try:
            commit_sha = run_git(["rev-list", "-n", "1", tag]).strip()
            tag_commit_map[tag] = commit_sha
        except Exception:
            continue
    return tag_commit_map


def _get_merge_commits(branch: str = "main") -> Dict[str, List[str]]:
    """Get merge commits and their parent branches - works locally."""
    merge_commits = {}

    try:
        # Get merge commits from local branch
        log_output = run_git(
            [
                "log",
                branch,
                "--merges",
                "--pretty=format:%H|%P|%s",
                "--reverse",
                "--max-count=50",  # Limit to recent merges
            ]
        ).splitlines()

        for line in log_output:
            if not line.strip():
                continue
            parts = line.split("|", 2)
            if len(parts) < 3:
                continue

            commit_sha, parents, message = parts
            parent_list = parents.split()
            if len(parent_list) > 1:
                merge_commits[commit_sha] = {"parents": parent_list, "message": message}
    except Exception as e:
        print(f"Warning: Could not get merge commits: {e}")

    return merge_commits


def _get_branch_names() -> List[str]:
    """Get all local branch names."""
    try:
        branches = run_git(["branch", "--format=%(refname:short)"]).splitlines()
        return [b.strip() for b in branches if b.strip()]
    except Exception:
        return ["main"]


def _is_ancestor(commit1: str, commit2: str) -> bool:
    """Check if commit1 is an ancestor of commit2."""
    try:
        result = run_git(["merge-base", "--is-ancestor", commit1, commit2])
        return True
    except Exception:
        return False


def generate_simple_release_graph(main_branch: str = "main", max_tags: int = 10) -> str:
    """Simple and reliable graph showing tags on main branch."""

    # Get tags reachable from main branch
    try:
        tags = run_git(["tag", "--merged", main_branch, "--sort=-creatordate"]).splitlines()
    except Exception:
        # Fallback: get all tags
        tags = run_git(["tag", "--sort=-creatordate"]).splitlines()

    if not tags:
        return '```mermaid\ngitGraph\n    commit id: "initial"\n```'

    # Take the most recent tags
    recent_tags = tags[:max_tags] if len(tags) > max_tags else tags

    graph_lines = ["```mermaid", "gitGraph"]

    # Start with initial commit
    graph_lines.append('    commit id: "initial"')

    # Add each tag as a commit on main
    for i, tag in enumerate(recent_tags):
        try:
            # Get the actual commit message for the tag
            commit_msg = run_git(["log", "-1", "--pretty=format:%s", tag])
            short_msg = _short_msg(commit_msg, 20)
            graph_lines.append(f'    commit id: "v{tag} {short_msg}" tag: "{tag}"')
        except Exception:
            # Fallback: just use tag name
            graph_lines.append(f'    commit id: "v{tag}" tag: "{tag}"')

    graph_lines.append("```")
    return "\n".join(graph_lines)


def generate_branch_based_graph(main_branch: str = "main", max_items: int = 15) -> str:
    """Graph based on branch structure rather than merge commits."""

    graph_lines = ["```mermaid", "gitGraph"]
    graph_lines.append('    commit id: "initial"')

    # Get recent branches (excluding main)
    try:
        branches = _get_branch_names()
        feature_branches = [b for b in branches if b != main_branch and not b.startswith("origin/")]

        # Limit to recent branches
        feature_branches = feature_branches[:5]  # Max 5 branches for readability

        for i, branch in enumerate(feature_branches):
            try:
                # Get last commit message on branch
                commit_msg = run_git(["log", "-1", "--pretty=format:%s", branch])
                short_msg = _short_msg(commit_msg, 15)

                graph_lines.append(f"    branch {branch}")
                graph_lines.append(f"    checkout {branch}")
                graph_lines.append(f'    commit id: "{short_msg}"')
                graph_lines.append(f"    checkout {main_branch}")
                graph_lines.append(f'    merge {branch} id: "merge-{i + 1}"')
            except Exception:
                continue

    except Exception as e:
        print(f"Warning: Could not generate branch graph: {e}")
        # Fallback to simple graph
        return generate_simple_release_graph(main_branch, max_items)

    graph_lines.append("```")
    return "\n".join(graph_lines)


def generate_commit_based_graph(main_branch: str = "main", max_commits: int = 20) -> str:
    """Graph based on recent commits with branch-like structure."""

    graph_lines = ["```mermaid", "gitGraph"]
    graph_lines.append('    commit id: "initial"')

    try:
        # Get recent commits
        commits = run_git(
            [
                "log",
                main_branch,
                "--pretty=format:%h|%s",
                "--max-count",
                str(max_commits),
                "--reverse",
            ]
        ).splitlines()

        # Group commits into "features"
        features = []
        current_feature = []

        for line in commits:
            if not line.strip():
                continue
            commit_hash, message = line.split("|", 1)
            short_msg = _short_msg(message, 15)

            # Simple heuristic: feat commits start new features
            if "feat:" in message.lower() and current_feature:
                features.append(current_feature)
                current_feature = []

            current_feature.append((commit_hash, short_msg))

        if current_feature:
            features.append(current_feature)

        # Create graph from features
        for i, feature in enumerate(features[:3]):  # Max 3 features for readability
            branch_name = f"feature-{i + 1}"
            graph_lines.append(f"    branch {branch_name}")
            graph_lines.append(f"    checkout {branch_name}")

            for commit_hash, short_msg in feature:
                graph_lines.append(f'    commit id: "{short_msg}"')

            graph_lines.append(f"    checkout {main_branch}")
            graph_lines.append(f'    merge {branch_name} id: "merge-{i + 1}"')

    except Exception as e:
        print(f"Warning: Could not generate commit graph: {e}")
        return generate_simple_release_graph(main_branch, max_commits)

    graph_lines.append("```")
    return "\n".join(graph_lines)


def write_graph_to_readme(readme: Path, heading: str, content: str):
    """Replace or create graph section in README."""
    if not readme.exists():
        # Create basic README if it doesn't exist
        basic_readme = f"""# Versioning Tool

{heading}

{content}
"""
        readme.write_text(basic_readme, encoding="utf-8")
        return

    text = readme.read_text(encoding="utf-8")
    marker = f"## {heading}"

    # Find the section
    start = text.find(marker)
    if start == -1:
        # Append to end if section doesn't exist
        new_text = text.rstrip() + f"\n\n{marker}\n\n{content}\n"
    else:
        # Replace existing section
        end = text.find("\n## ", start + 1)
        if end == -1:
            # Replace to end of file
            new_text = text[:start] + f"{marker}\n\n{content}\n"
        else:
            # Replace the section
            new_text = text[:start] + f"{marker}\n\n{content}\n" + text[end:]

    readme.write_text(new_text, encoding="utf-8")


def get_graph_type_choice() -> str:
    """Prompt user for graph type choice."""
    print("Choose graph type:")
    print("1. Simple release (tags only) - Most reliable")
    print("2. Branch-based (local branches)")
    print("3. Commit-based (recent commits)")

    choice = input("Enter choice (1-3, default=1): ").strip()
    if choice == "2":
        return "branch"
    elif choice == "3":
        return "commit"
    else:
        return "simple"


def graph_for_main(
    main_branch: str = "main", max_items: int = 12, graph_type: str = "simple"
) -> str:
    """Generate appropriate graph based on type choice."""
    if graph_type == "branch":
        return generate_branch_based_graph(main_branch, max_items)
    elif graph_type == "commit":
        return generate_commit_based_graph(main_branch, max_items)
    else:
        return generate_simple_release_graph(main_branch, max_items)


# Test function to debug your git environment
def debug_git_environment():
    """Debug function to see what git commands work."""
    print("=== Git Environment Debug ===")

    try:
        print("Branches:", run_git(["branch", "-a"]))
    except Exception as e:
        print(f"Branches error: {e}")

    try:
        print("Tags:", run_git(["tag", "--list"]))
    except Exception as e:
        print(f"Tags error: {e}")

    try:
        print("Remote branches:", run_git(["branch", "-r"]))
    except Exception as e:
        print(f"Remote branches error: {e}")

    try:
        print("Merge commits:", run_git(["log", "--oneline", "--merges", "-5"]))
    except Exception as e:
        print(f"Merge commits error: {e}")
