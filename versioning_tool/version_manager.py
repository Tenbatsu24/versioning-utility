import re
import sys
import yaml
import fnmatch
import subprocess

from pathlib import Path

from packaging.version import Version, InvalidVersion

try:
    import tomllib  # Python 3.11+
except ImportError:
    # Fallback for 3.6 < Python < 3.11
    import tomli as tomllib  # type: ignore[import]

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from versioning_tool.config import PYPROJECT_FILE, VERSIONING_CONFIG

console = Console()


def print_info_panel(message: str, title: str = "ℹ️ Info", border_style: str = "blue"):
    console.print(Panel(message, title=title, border_style=border_style, expand=False))


def load_versioning_config(path: Path):
    if not path.exists():
        console.print(
            Panel(
                f"Versioning configuration file {path} not found. Using default settings.",
                title="⚠️ Warning",
                border_style="yellow",
                expand=False,
            )
        )
        return {}
    console.print(
        Panel(
            f"Loading versioning configuration from {path}",
            title="ℹ️ Loading Config",
            border_style="blue",
            expand=False,
        )
    )
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_version_from_pyproject(file_path: Path):
    try:
        with file_path.open("rb") as f:
            data = tomllib.load(f)
            return data["project"]["version"]
    except Exception as e:
        console.print(f"[bold red]Error reading {file_path}: {e}[/bold red]")
        return None


def update_pyproject_version(file_path: Path, new_version: str):
    try:
        with file_path.open("r", encoding="utf-8") as f:
            content = f.read()
        content_new = re.sub(
            r'version\s*=\s*"[0-9A-Za-z.\-]+"', f'version = "{new_version}"', content
        )
        with file_path.open("w", encoding="utf-8") as f:
            f.write(content_new)

        print_info_panel(
            f"Updated pyproject.toml to version {new_version}",
            "✅ Version Updated",
            "green",
        )
    except Exception as e:
        print_info_panel(f"Failed to update pyproject.toml: {e}", "❌ Error", "red")
        sys.exit(1)


def get_current_branch():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Failed to get current branch: {e}[/bold red]")
        sys.exit(1)


def get_main_version(default_branch="main"):
    try:
        result = subprocess.run(
            ["git", "show", f"origin/{default_branch}:pyproject.toml"],
            capture_output=True,
            text=True,
            check=True,
        )
        import io

        data = tomllib.load(io.BytesIO(result.stdout.encode()))
        if "project" not in data or "version" not in data["project"]:
            # assume this is the first version
            console.print(
                Panel(
                    "No version found in main branch pyproject.toml. Assuming first version (0.0.0).",
                    title="ℹ️ Info",
                    border_style="blue",
                    expand=False,
                )
            )
            return "0.0.0"
        if not isinstance(data["project"]["version"], str):
            console.print(
                Panel(
                    "Invalid version format in main branch pyproject.toml.",
                    title="❌ Error",
                    border_style="red",
                    expand=False,
                )
            )
            sys.exit(1)
        if not re.match(
            r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+(\.\d+)?)?$", data["project"]["version"]
        ):
            console.print(
                Panel(
                    "Version in main branch pyproject.toml does not match semantic versioning.",
                    title="❌ Error",
                    border_style="red",
                    expand=False,
                )
            )
            sys.exit(1)
        return data["project"]["version"]
    except subprocess.CalledProcessError as e:
        console.print(
            Panel(
                f"Failed to get main branch version: {e}",
                title="❌ Error",
                border_style="red",
                expand=False,
            )
        )
        sys.exit(1)
    except Exception as e:
        console.print(
            Panel(
                f"Failed to parse main branch pyproject.toml: {e}",
                title="❌ Error",
                border_style="red",
                expand=False,
            )
        )
        sys.exit(1)


def get_commits_since_main(default_branch="main"):
    try:
        result = subprocess.run(
            ["git", "log", f"origin/{default_branch}..HEAD", "--pretty=format:%s"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Failed to get commits: {e}[/bold red]")
        return []


def suggest_next_version(current_version: str | None, pre_release: str | None = None):
    try:
        ver = Version(current_version)
    except InvalidVersion:
        console.print(
            f"[bold red]Invalid current version: {current_version}[/bold red]"
        )
        sys.exit(1)

    if pre_release:
        if ver.pre and ver.pre[0] == pre_release:
            new_pre = (pre_release, ver.pre[1] + 1)
        else:
            new_pre = (pre_release, 1)
        new_version = f"{ver.major}.{ver.minor}.{ver.micro}-{new_pre[0]}.{new_pre[1]}"
    else:
        new_version = f"{ver.major}.{ver.minor}.{ver.micro + 1}"
    return new_version


def get_pre_release_for_branch(branch: str, branch_mappings: dict) -> str | None:
    for pattern, pre in branch_mappings.items():
        if fnmatch.fnmatch(branch, pattern):
            return pre
    return None


def print_version_warning(branch, current_version, suggested_version):
    table = Table(show_header=False, box=None)
    table.add_row("Branch:", branch)
    table.add_row("Current version:", current_version)
    table.add_row("Suggested version:", suggested_version)
    table.add_row("", "Please update pyproject.toml before pushing!")

    console.print(
        Panel(
            table,
            title="⚠️  VERSION NOT BUMPED ⚠️",
            border_style="bold red",
            style="bold white on red",
            expand=False,
        )
    )


def print_auto_bump_panel(branch, old_version, new_version):
    table = Table(show_header=False, box=None)
    table.add_row("Branch:", branch)
    table.add_row("Old version:", old_version)
    table.add_row("New version:", new_version)
    table.add_row("", "This version was auto-bumped based on commits!")

    console.print(
        Panel(
            table,
            title="🚨 VERSION AUTO-BUMPED 🚨",
            border_style="bold yellow",
            style="bold black on yellow",
            expand=True,
        )
    )


def main():
    branch = get_current_branch()
    current_version = get_version_from_pyproject(PYPROJECT_FILE)
    if not current_version:
        print_info_panel("Could not read current version.", "❌ Error", "red")
        sys.exit(1)

    main_version = get_main_version()
    if not main_version:
        print_info_panel("Could not read main branch version.", "❌ Error", "red")
        sys.exit(1)

    # load the versioning config\
    versioning_config = load_versioning_config(VERSIONING_CONFIG)
    if not versioning_config:
        print_info_panel(
            "No versioning configuration found. Using default settings.",
            "ℹ️ Info",
            "blue",
        )
        versioning_config = {
            "default_branch": "main",
            "pre_release_branches": {
                "feature/*": "alpha",
                "beta/*": "beta",
                "rc/*": "rc",
            },
        }

    pre_release = get_pre_release_for_branch(
        branch, versioning_config.get("pre_release_branches", {})
    )
    if pre_release:
        print_info_panel(
            f"Detected pre-release type: {pre_release}",
            "ℹ️ Pre-release Type",
            "blue",
        )
    else:
        print_info_panel(
            "No pre-release type detected. Assuming stable release.",
            "ℹ️ Stable Release",
            "blue",
        )

    # Compute suggested version
    if pre_release:
        if f"{pre_release}" not in current_version:
            suggested = suggest_next_version(main_version, pre_release)
            print_version_warning(branch, current_version, suggested)
            update_pyproject_version(PYPROJECT_FILE, suggested)

            # Update changelog automatically for pre-release
            subprocess.run(
                [
                    "venv/bin/python",
                    "versioning_tool/changelog_generator.py",
                    suggested,
                ],
                check=True,
            )

            warning_table = Table(show_header=False, box=None)
            warning_table.add_row("Branch:", branch)
            warning_table.add_row("Old version:", current_version)
            warning_table.add_row("New version:", suggested)
            warning_table.add_row("", "This pre-release version was auto-bumped!")

            console.print(
                Panel(
                    warning_table,
                    title="🚨 PRE-RELEASE VERSION AUTO-BUMPED 🚨",
                    border_style="bold yellow",
                    style="bold black on yellow",
                    expand=True,
                )
            )
        else:
            print_info_panel(
                f"Pre-release version {current_version} looks good.",
                "✅ Pre-release OK",
                "green",
            )
    else:
        if current_version == main_version:
            suggested = suggest_next_version(current_version)
            print_version_warning(branch, current_version, suggested)

            response_panel = Panel(
                f"Do you want to auto-bump to {suggested}? [y/N]: ",
                title="❓ Auto-bump Confirmation",
                border_style="cyan",
            )
            response = input(response_panel.renderable)  # show panel and get input
            if response.lower() == "y":
                update_pyproject_version(PYPROJECT_FILE, suggested)
                print_info_panel(
                    f"Version bumped to {suggested}", "✅ Version Bumped", "green"
                )
                subprocess.run(
                    [
                        "venv/bin/python",
                        "versioning_tool/changelog_generator.py",
                        suggested,
                    ],
                    check=True,
                )
            else:
                print_info_panel(
                    "Version not changed.", "⚠️ Version Not Changed", "yellow"
                )
                sys.exit(1)
        else:
            print_info_panel(
                f"Version bumped: {main_version} → {current_version}",
                "✅ Version OK",
                "green",
            )


if __name__ == "__main__":
    main()
