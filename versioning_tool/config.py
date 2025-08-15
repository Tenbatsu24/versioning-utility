from pathlib import Path

PROJ_ROOT = Path(__file__).parent.parent.resolve()
CHANGELOG_FILE = PROJ_ROOT / "CHANGELOG.md"
PYPROJECT_FILE = PROJ_ROOT / "pyproject.toml"
VERSIONING_CONFIG = PROJ_ROOT / "versioning.yaml"
