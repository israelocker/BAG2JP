"""Configured host inputs for the BAG1 import scripts; no location defaults live here."""
from functools import lru_cache
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.workflow.project_config import ProjectConfig, load_config, require_paths  # noqa: E402


@lru_cache(maxsize=1)
def _project_config() -> ProjectConfig:
    return load_config(repo_root=ROOT)


def input_path(key: str, *, config: ProjectConfig | None = None) -> Path:
    """Return the path registered under ``key``; a missing key raises ConfigError."""
    path, = require_paths(config if config is not None else _project_config(), (key,))
    return path


def project_label(path: Path, root: Path = ROOT) -> str:
    """Portable provenance text: project-relative inside the project, absolute outside it."""
    path, root = Path(path).resolve(), Path(root).resolve()
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
