"""Where the large files live. The data root is on an external drive and is never in git.

Set it once per machine, either in `paths.local.toml` at the repository root:
    data_root = "<data>"
or with the environment variable KAGML_DATA (which wins).
"""
import os
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def data_root() -> Path:
    root = os.environ.get("KAGML_DATA")
    local = REPO / "paths.local.toml"
    if not root and local.exists():
        root = tomllib.loads(local.read_text(encoding="utf-8")).get("data_root")
    if not root:
        raise SystemExit("No data root: set KAGML_DATA or data_root in paths.local.toml (see src/kagml/paths.py).")
    path = Path(root)
    if not path.exists():
        raise SystemExit(f"Data root {path} not found: is the external drive plugged in?")
    return path


def raw_replays(submission: int | str) -> Path:
    return data_root() / "raw" / "replays" / str(submission)


def datasets() -> Path:
    return data_root() / "datasets"


def models() -> Path:
    return data_root() / "models"


def runs() -> Path:
    return data_root() / "runs"
