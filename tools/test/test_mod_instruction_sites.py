"""Main-executable instruction plugins must be opted in to native code generation.

The runtime only calls instruction plugins from AOT code for sites listed in
[recompiler] mod_instruction_sites (psxrecomp/runtime/include/mod_plugins.h).
Overlay sites run through the guarded dirty-RAM interpreter and need no opt-in.
"""
from pathlib import Path
import re
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODS = ROOT / 'mods-src'
CONFIG = ROOT / 'patches' / 'BAG2JP-game.toml'
BUILD_GENERATED = Path('D:/Dev/Recomp/BAG2JP-codex-build/BAG2JP/generated')
MAIN_TEXT = range(0x80010000, 0x80010000 + 0x4D000)  # load_address + text_size
# Known main-executable sites that intentionally (or pending an owner decision) stay unlisted.
UNLISTED = {
    0x80049F94: 'anim-trace probe rewrites its code word, so the dirty-RAM interpreter runs it',
    0x80014FB8: 'BAG1 stage camera clamp: never opted in natively, enabling it changes the camera',
    0x80014FD4: 'BAG1 stage camera offset: never opted in natively, enabling it changes the camera',
}
CALL = re.compile(r'psx_mod_register_instruction_plugin\(\s*[^,]+,\s*([^,]+?)\s*,', re.S)
DEFINE = re.compile(r'#define\s+(\w+)\s+\(?\s*(0x[0-9A-Fa-f]+)u?\b')


def registered_sites():
    sources = list(MODS.rglob('*.c')) + list(MODS.rglob('*.h'))
    defines = {}
    for path in sources:
        for name, value in DEFINE.findall(path.read_text(errors='replace')):
            defines.setdefault(name, set()).add(int(value, 16))
    sites = {}
    for path in sources:
        for token in CALL.findall(path.read_text(errors='replace')):
            token = token.strip()
            values = {int(token.rstrip('uU'), 16)} if token.startswith('0x') else defines.get(token)
            assert values, f'{path.name}: cannot resolve instruction site {token}'
            for value in values:
                sites[value] = path.name
    return sites


def listed_sites():
    recompiler = tomllib.loads(CONFIG.read_text())['recompiler']
    return {int(site, 16) for site in recompiler.get('mod_instruction_sites', [])}


class ModInstructionSitesTest(unittest.TestCase):
    def test_resident_pack_latch_is_registered(self):
        self.assertEqual(registered_sites().get(0x8001F8A4), 'bag2jp_bag1_versions.c')

    def test_main_executable_sites_are_opted_in(self):
        main = {site: name for site, name in registered_sites().items() if site in MAIN_TEXT}
        missing = {hex(site): name for site, name in main.items()
                   if site not in listed_sites() and site not in UNLISTED}
        self.assertEqual(missing, {})

    def test_listed_sites_are_registered_main_executable_sites(self):
        registered = registered_sites()
        for site in listed_sites():
            self.assertIn(site, MAIN_TEXT)
            self.assertIn(site, registered)
            self.assertNotIn(site, UNLISTED)

    def test_exceptions_are_still_registered_main_executable_sites(self):
        registered = registered_sites()
        for site in UNLISTED:
            self.assertIn(site, MAIN_TEXT)
            self.assertIn(site, registered)

    @unittest.skipUnless(BUILD_GENERATED.is_dir(), 'build tree not present')
    def test_build_generated_code_calls_listed_sites(self):
        text = ''.join(p.read_text(errors='replace') for p in BUILD_GENERATED.glob('*.c'))
        for site in listed_sites():
            self.assertRegex(text, rf'psx_mod_instruction\(cpu, 0x{site:08X}u, 0x[0-9A-F]{{8}}u\);')
        # The controller is emitted through two generated paths, both need the seam.
        self.assertEqual(text.count('psx_mod_instruction(cpu, 0x8002D818u, 0x8E660038u);'), 2)


if __name__ == '__main__':
    unittest.main()
