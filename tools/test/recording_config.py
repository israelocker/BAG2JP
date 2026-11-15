"""Recorder-specific immutable view of the shared host resolver; no TOML parser."""
from dataclasses import dataclass
from pathlib import Path
import re

from tools.workflow.project_config import (
    ConfigError, ProjectConfig, assert_write_target, export_config, load_config,
    recording_overrides, require_paths, require_values,
)


@dataclass(frozen=True)
class RecordingSettings:
    config: ProjectConfig
    operation: str
    recordings: Path
    game_dir: Path | None
    fps: int | None
    max_seconds: float | None

    def value(self, name: str):
        return require_values(self.config, (f"recording.{name}",))[0]

    def tool(self, name: str) -> Path:
        key = f"tools.{name}"
        path, = require_paths(self.config, (key,))
        if not path.is_file():
            raise ConfigError(f"{key}: configured file does not exist: {path}")
        return path

    def output(self, tag: str) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", tag):
            raise ConfigError("tag: use 1-64 ASCII letters, digits, _ or -")
        return self.target(self.recordings / tag)

    def target(self, path: Path) -> Path:
        return assert_write_target(self.config, path, role="work")

    def file_target(self, path: Path) -> Path:
        target = self.target(path)
        if target.exists() and not target.is_file():
            raise ConfigError(f"Expected a file write target: {target}")
        return target

    def for_operation(self, operation: str):
        """Validate supplied settings before effects without re-reading any inputs."""
        resolved = resolve_settings(self.config, operation=operation, environ={})
        return self if self.operation == operation else resolved

    def provenance(self) -> dict:
        return export_config(self.config, operation=f"recording-{self.operation}")

    def for_capture(self, fps, max_seconds, game_dir):
        """Bind explicit Python arguments without re-reading files or the environment."""
        valid_types = type(fps) is int and type(max_seconds) in (int, float)
        if self.operation == "record" and valid_types and (fps, max_seconds, game_dir) == (self.fps, self.max_seconds, self.game_dir):
            return self
        return resolve_settings(self.config, environ={},
                                fps=fps if type(fps) is not int or fps != self.fps else None,
                                max_seconds=max_seconds if type(max_seconds) not in (int, float)
                                or max_seconds != self.max_seconds else None,
                                game_dir=game_dir if game_dir != self.game_dir else None)


def resolve_settings(config: ProjectConfig | None = None, *, operation: str = "record",
                     environ=None, fps=None, max_seconds=None, game_dir=None) -> RecordingSettings:
    config = recording_overrides(load_config() if config is None else config,
                                 environ=environ if operation == "record" else {},
                                 fps=fps, max_seconds=max_seconds, game_dir=game_dir)
    payload = export_config(config, operation=f"recording-{operation}")
    if payload["missing"]:
        raise ConfigError("Unresolved recording fields: " + ", ".join(payload["missing"]))
    work, = require_paths(config, ("paths.work_root",))
    recordings = assert_write_target(config, work / "recordings", role="work")
    game = None
    if operation == "record":
        game, = require_paths(config, ("paths.experimental_install",))
    settings = RecordingSettings(config, operation, recordings, game,
                                 config.values.get("recording.fps"), config.values.get("recording.max_seconds"))
    if operation == "finalize":
        for name in ("ffmpeg_review", "ffprobe_review", "recording_font"):
            settings.tool(name)
    elif operation == "frames":
        settings.tool("ffmpeg_look")
    return settings
