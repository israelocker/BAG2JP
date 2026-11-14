"""Direct arithmetic bounds and old-framework compatibility for bubble radii."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def linux_path(path: Path) -> str:
    """Convert a path for this project's recorded WSL C compiler."""
    return "/mnt/" + path.drive[0].lower() + path.as_posix()[2:]


class GasoBubbleTest(unittest.TestCase):
    def test_api_compatibility_and_radius_bounds(self) -> None:
        """Compile both availability branches; guard tiny/extreme radii/aspects."""
        with tempfile.TemporaryDirectory(dir=ROOT / "_work") as folder_name:
            folder = Path(folder_name)
            source = folder / "bubble.c"
            source.write_text('''
#include <assert.h>
#include <stdint.h>
#include <limits.h>
#if HAVE_QUERY
#define PSX_MOD_DISPLAY_PIXEL_ASPECT 1
static uint32_t n = 5, d = 6;
static int available = 1;
static int psx_mod_display_pixel_aspect(uint32_t *pn, uint32_t *pd) {
    *pn = n; *pd = d; return available;
}
#endif
#include "bag2jp_gaso_bubble.h"
int main(void) {
    int32_t x = 99, y = 99;
#if HAVE_QUERY
    assert(gaso_bubble_screen_radii(68,1000,6000,&x,&y) && x==13 && y==11);
    assert(gaso_bubble_screen_radii(17,1000,6000,&x,&y) && x==2 && y==2);
    d=8;
    assert(gaso_bubble_screen_radii(68,1000,6000,&x,&y) && x==17 && y==11);
    d=0;
    assert(!gaso_bubble_screen_radii(68,1000,6000,&x,&y) && x==0 && y==0);
    n=1; d=UINT32_MAX;
    assert(!gaso_bubble_screen_radii(68,1000,6000,&x,&y) && x==0 && y==0);
    n=UINT32_MAX; d=1;
    assert(!gaso_bubble_screen_radii(68,1000,6000,&x,&y) && x==0 && y==0);
    n=5; d=6;
    assert(!gaso_bubble_screen_radii(INT32_MAX,INT32_MAX,1,&x,&y));
    assert(!gaso_bubble_screen_radii(1,1,6000,&x,&y));
    assert(!gaso_bubble_screen_radii(0,1000,6000,&x,&y));
    assert(!gaso_bubble_screen_radii(68,0,6000,&x,&y));
    assert(!gaso_bubble_screen_radii(68,1000,0,&x,&y));
    assert(!gaso_bubble_screen_radii(68,1000,6000,0,&y));
    assert(!gaso_bubble_screen_radii(68,1000,6000,&x,0));
    available=0;
#endif
    assert(!gaso_bubble_screen_radii(68,1000,6000,&x,&y) && x==0 && y==0);
    return 0;
}
''', encoding="utf-8")
            for available in (0, 1):
                with self.subTest(query_available=available):
                    binary = folder / "bubble"
                    subprocess.run([
                        "wsl.exe", "-d", "Ubuntu", "--exec", "gcc", "-std=c11",
                        "-Wall", "-Wextra", "-Werror", f"-DHAVE_QUERY={available}",
                        "-I" + linux_path(ROOT / "mods-src/bag2jp.feature.bag1-content"),
                        linux_path(source), "-o", linux_path(binary),
                    ], check=True)
                    result = subprocess.run([
                        "wsl.exe", "-d", "Ubuntu", "--exec", linux_path(binary)
                    ], capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
