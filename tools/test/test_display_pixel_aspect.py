"""Host seam for the read-only framework presentation query.

Compiles the actual GPU query and mod API forwarding body, with only display/
classifier inputs stubbed. Does not compile or validate the complete renderer.
The pinned local build tree is an explicit external fixture for this project.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT.parent / "BAG2JP-codex-build/BAG2JP/psxrecomp/runtime"


def linux_path(path: Path) -> str:
    """Convert a local path for the recorded WSL compiler."""
    return "/mnt/" + path.drive[0].lower() + path.as_posix()[2:]


def extract_function(path: Path, signature: str) -> str:
    """Extract the actual function, balancing braces, not a rewritten model."""
    text = path.read_text(encoding="utf-8")
    start = text.index(signature)
    opening = text.index("{", start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return text[start:end].replace('extern "C" ', "", 1)


class DisplayPixelAspectTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """Compile the public forwarding seam and actual GPU query in C11."""
        gpu = extract_function(RUNTIME / "src/gpu.c", "int gpu_display_pixel_aspect(")
        api = extract_function(RUNTIME / "src/mod_runtime.cpp",
                               'extern "C" int psx_mod_display_pixel_aspect(')
        cls.folder = tempfile.TemporaryDirectory(dir=ROOT / "_work")
        cls.addClassCleanup(cls.folder.cleanup)
        folder = Path(cls.folder.name)
        cls.binary = folder / "aspect"
        source = folder / "aspect.c"
        source.write_text('''
#include <assert.h>
#include <stdint.h>
#include <limits.h>
#include <stdlib.h>
#include <string.h>
typedef struct { uint32_t width, height; int disabled, depth24; } GpuDisplayInfo;
static GpuDisplayInfo display = {512, 240, 0, 0};
static int ws_cfg_num = 16, ws_cfg_den = 9;
static int ws_local_viewport_cfg, native43, wide_active, offset = 85;
static void gpu_get_display_info(GpuDisplayInfo *p) { *p = display; }
static int gpu_ws_present_native_43(void) { return native43; }
static int ws_native_wide_active(void) { return wide_active; }
static int ws_nw_offset(void) { return offset; }
''' + gpu + "\n" + api + '''
int main(int argc, char **argv) {
    assert(argc == 2);
    int scenario = atoi(argv[1]);
    uint32_t n = 99, d = 99;
    if (scenario == 1) native43 = 1;
    if (scenario == 2) { ws_cfg_num = 21; ws_cfg_den = 9; }
    if (scenario == 3) wide_active = 1;
    if (scenario == 4) display.width = 0;
    if (scenario == 5) display.height = 0;
    if (scenario == 6) display.disabled = 1;
    if (scenario == 7) ws_local_viewport_cfg = 1;
    if (scenario == 8) ws_cfg_den = 0;
    if (scenario == 9) {
        assert(!psx_mod_display_pixel_aspect(0, &d) && d == 0); return 0;
    }
    if (scenario == 10) {
        assert(!psx_mod_display_pixel_aspect(&n, &n) && n == 0); return 0;
    }
    if (scenario == 11) { display.width = 320; display.height = 240; native43 = 1; }
    if (scenario == 12) { display.width = 640; display.height = 480; native43 = 1; }
    if (scenario == 13) display.depth24 = 1;
    if (scenario == 14) {
        assert(!psx_mod_display_pixel_aspect(&n, 0) && n == 0); return 0;
    }
    if (scenario == 15) ws_cfg_num = -1;
    if (scenario == 16) { wide_active = 1; offset = -1; }
    if (scenario == 17) { native43 = 1; ws_cfg_den = 0; }
    if ((scenario >= 4 && scenario <= 8) || scenario == 13 || scenario >= 15) {
        assert(!psx_mod_display_pixel_aspect(&n, &d) && n == 0 && d == 0);
        return 0;
    }
    assert(psx_mod_display_pixel_aspect(&n, &d));
    if (scenario == 0) assert(n == 5 && d == 6); /* stretched16:9 */
    if (scenario == 1) assert(n == 5 && d == 8); /* native4:3 */
    if (scenario == 2) assert(n == 35 && d == 32); /* stretched21:9 */
    if (scenario == 3) assert(n == 640 && d == 1023); /* 682-wide native-wide */
    if (scenario == 11 || scenario == 12) assert(n == 1 && d == 1);
    /* The query must not change the source aspect or geometry. */
    assert(ws_cfg_num == (scenario == 2 ? 21 : 16) && ws_cfg_den == 9);
    return 0;
}
''', encoding="utf-8")
        subprocess.run(["wsl.exe", "-d", "Ubuntu", "--exec", "gcc", "-std=c11",
                        "-Wall", "-Werror", "-Wno-unused-function", "-Wno-unused-variable",
                        linux_path(source), "-o", linux_path(cls.binary)], check=True)

    def test_presentation_query(self) -> None:
        """Use independent aspect values, invalid inputs and presentation modes."""
        for scenario in range(18):
            with self.subTest(scenario=scenario):
                result = subprocess.run(["wsl.exe", "-d", "Ubuntu", "--exec",
                                         linux_path(self.binary), str(scenario)],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
