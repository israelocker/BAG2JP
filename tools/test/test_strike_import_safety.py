"""Safety checks that prevent deployment from unverified Strike assumptions."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PROJECT = Path(__file__).parents[2]


class StrikeImportSafetyTests(unittest.TestCase):
    def test_animation_builder_rejects_unaccepted_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "animations.bin"
            result = subprocess.run(
                [
                    sys.executable,
                    str(PROJECT / "tools/bag1import/anim_remap_strike.py"),
                    str(PROJECT / "_work/character_inventory/strike/001.bin"),
                    str(output),
                ],
                cwd=PROJECT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())
            self.assertIn("policy is not accepted", result.stderr)


if __name__ == "__main__":
    unittest.main()
