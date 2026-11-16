"""Real resolver fixture with isolated paths and explicit installed media tools."""
import json
from pathlib import Path
import shutil

from tools.test.recording_config import resolve_settings
from tools.workflow.project_config import load_config


def recorder_settings(root: Path, *, operation="record", environ=None):
    root = root.resolve()
    repo = root / "host-config"
    (repo / "config").mkdir(parents=True, exist_ok=True)
    source = Path(__file__).resolve().parents[2] / "config/project.toml"
    (repo / "config/project.toml").write_bytes(source.read_bytes())
    paths = {"work_root": str(root), "stable_install": str(root / "stable"),
             "experimental_install": str(root)}
    tools = {"ffmpeg_review": shutil.which("ffmpeg"), "ffprobe_review": shutil.which("ffprobe"),
             "recording_font": "fonts/consola.ttf", "ffmpeg_wgc": str(root / "absent-wgc.exe")}
    local = "[paths]\n" + "".join(f"{key}={json.dumps(value)}\n" for key, value in paths.items())
    local += "[tools]\n" + "".join(f"{key}={json.dumps(value)}\n" for key, value in tools.items() if value)
    (repo / "config/project.local.toml").write_text(local, encoding="utf-8", newline="\n")
    settings = resolve_settings(load_config(repo_root=repo), operation=operation,
                                environ={} if environ is None else environ)
    settings.recordings.mkdir(parents=True, exist_ok=True)
    return settings
