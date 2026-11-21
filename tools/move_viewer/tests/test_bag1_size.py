"""Host test of the real bag1-content size bound (b1v_accept_size), compiled with WSL gcc."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HEADER = ROOT / 'mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_size.h'
STOCK = 336300  # Strike entry 109 compiled size

PROGRAM = r'''
#include <stdio.h>
#include "bag2jp_bag1_size.h"
int main(void) {
    const unsigned stock = %d;
    const unsigned seen[] = {stock - 1, stock, stock + 1, stock + B1V_MAX_GROWTH,
                             stock + B1V_MAX_GROWTH + 1, 0, 0xFFFFFFFFu};
    for (unsigned i = 0; i < sizeof seen / sizeof seen[0]; ++i)
        printf("%%u %%u\n", seen[i], b1v_accept_size(seen[i], stock));
    return 0;
}
'''


def wsl_path(path: Path) -> str:
    drive, rest = str(path.resolve()).split(':', 1)
    return f'/mnt/{drive.lower()}{rest.replace(chr(92), "/")}'


@unittest.skipUnless(shutil.which('wsl'), 'WSL gcc required')
class AcceptSizeTest(unittest.TestCase):
    def test_bound_is_inclusive_and_rejects_everything_else(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / 'probe.c'
            src.write_text(PROGRAM % STOCK)
            shutil.copy(HEADER, tmp)
            out = subprocess.run(
                ['wsl', '-e', 'sh', '-c',
                 f'cd "{wsl_path(Path(tmp))}" && gcc -std=c11 -Wall -Werror -o probe probe.c && ./probe'],
                capture_output=True, text=True, check=True).stdout
        got = dict(tuple(map(int, line.split())) for line in out.splitlines())
        bound = STOCK + 4388
        self.assertEqual(got, {STOCK - 1: STOCK, STOCK: STOCK, STOCK + 1: STOCK + 1,
                               bound: bound, bound + 1: STOCK, 0: STOCK,
                               0xFFFFFFFF: STOCK})


if __name__ == '__main__':
    unittest.main()
