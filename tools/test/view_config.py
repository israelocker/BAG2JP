"""JSON adapter for view wrappers. Configuration and path guards have one authority."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.workflow import project_config as pc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation", required=True,
                        choices=("endings-view", "endings-acceptance", "dance-capture"))
    parser.add_argument("--local-config", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-exe", type=Path)
    parser.add_argument("--key-tool")
    parser.add_argument("--shot-tool")
    args = parser.parse_args(argv)
    try:
        config = pc.load_config(local_config=args.local_config)
        result = pc.export_config(config, operation=args.operation)
        if result["missing"]:
            raise pc.ConfigError("Missing configuration: " + ", ".join(result["missing"]))
        output = pc.assert_write_target(config, args.output, role="work")
        if args.operation == "endings-acceptance" and output.exists():
            raise pc.ConfigError("Preserve existing acceptance output")
        if args.operation == "dance-capture":
            if args.expected_exe is None:
                raise pc.ConfigError("--expected-exe is required for dance-capture")
            exe = args.expected_exe.resolve()
        else:
            (game,) = pc.require_paths(config, ("paths.experimental_install",))
            game = pc.assert_write_target(config, game, role="experimental")
            exe = game / "BAG2JP.exe"
        tools = None
        if args.key_tool is None or args.shot_tool is None:
            (tools,) = pc.require_paths(config, ("tools.winshot_root",))
        # Explicit helper overrides keep their existing caller/CWD semantics.
        result["effective"] = dict(output=str(output), exe=str(exe), game=str(exe.parent),
            key_tool=str(args.key_tool if args.key_tool is not None else tools / "postkey.ps1"),
            shot_tool=str(args.shot_tool if args.shot_tool is not None else tools / "winshot.ps1"))
    except pc.ConfigError as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
