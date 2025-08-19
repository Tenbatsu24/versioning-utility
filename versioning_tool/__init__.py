import os
from pathlib import Path

PROJ_ROOT = Path(__file__).parent.parent.resolve()

DEFAULT_CONFIG_PATH = PROJ_ROOT / "versioning.yml"
CFG_PATH = Path(os.getenv("VERSIONING_CONFIG_PATH", DEFAULT_CONFIG_PATH))
