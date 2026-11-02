"""Run under WSL Python: compile the real C plugin against a RAM/API test seam."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "_work" / "endings-view"
CASES = ("guest-address", "menu-order", "overlay-guard", "confirm", "cancel",
         "ending", "stock-selector", "native-lettering", "hd-lettering")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    binary = OUT / "test_endings_view"
    subprocess.run(["gcc", "-I" + str(ROOT / "tools/test/endings_view_stubs"),
                    str(ROOT / "tools/test/test_endings_view.c"), "-o", str(binary)], check=True)
    failed = 0
    for case in CASES:
        result = subprocess.run([str(binary), case], capture_output=True, text=True, cwd=OUT)
        (OUT / (case + ".log")).write_text(result.stdout + result.stderr)
        print(f"{case}: {'PASS' if result.returncode == 0 else 'FAIL'}")
        if result.returncode:
            failed += 1
            print(result.stderr.strip())
    print(f"{len(CASES) - failed}/{len(CASES)} passed")
    return bool(failed)


if __name__ == "__main__":
    sys.exit(main())
