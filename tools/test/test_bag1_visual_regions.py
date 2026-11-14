"""Regional payload packing and actual DF2 routing, without a game deployment."""
import importlib.util
from pathlib import Path
import struct
import subprocess
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "alt_exact", ROOT / "tools/bag1import/make_alt_entries_exact.py")
alt = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(alt)


class DiscFixture:
    """Real DF2 wire header, with a bounded synthetic DUMMY extent."""
    def walk(self):
        return [("BUST2.BIN", 10, 4096), ("DUMMY.BIN", 20, 8192)]

    def read(self, lba, size):
        if lba == 10:
            header = bytearray(size)
            header[:4] = b"DF2_"
            struct.pack_into("<I", header, 4, 2)
            struct.pack_into("<II", header, 16, 4096, 123)
            return bytes(header)
        assert lba == 20
        return b"\0" * size


class VisualRegionsTest(unittest.TestCase):
    def test_legacy_payload_bytes_are_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "legacy.dfs"
            source.write_bytes(b"legacy")
            payload, rows, _ = alt.build({"rows": [
                {"entry": 1, "chr": 9, "kind": 0, "file": str(source)}]}, DiscFixture())
            self.assertEqual(payload, b"legacy" + b"\0" * 2042)
            self.assertEqual(rows[0]["alt_off"], 20480)

    def test_regional_rows_keep_exact_sizes_and_deduplicate_identical_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            usa, jp = [Path(directory) / name for name in ("usa", "jp")]
            usa.write_bytes(b"USA")
            jp.write_bytes(b"JAPAN")
            row = {"entry": 1, "chr": 9, "kind": 0,
                   "regions": {"international": str(usa), "japanese": str(jp)}}
            payload, rows, _ = alt.build({"rows": [row]}, DiscFixture())
            self.assertEqual((rows[0]["alt_off"], rows[0]["alt_size"]), (20480, 3))
            self.assertEqual((rows[0]["jp_off"], rows[0]["jp_size"]), (22528, 5))
            self.assertEqual(payload[:3], b"USA")
            self.assertEqual(payload[2048:2053], b"JAPAN")
            jp.write_bytes(b"USA")
            payload, rows, _ = alt.build({"rows": [row]}, DiscFixture())
            self.assertEqual(len(payload), 2048)
            self.assertEqual(rows[0]["alt_off"], rows[0]["jp_off"])
            self.assertIn("jp_off, jp_size", alt.render_index(rows))

    def test_partial_or_ambiguous_regions_are_rejected(self):
        for regions in ({"japanese": "missing"}, {"international": "missing"}, {}):
            with self.subTest(regions=regions), self.assertRaisesRegex(ValueError, "regions"):
                alt.build({"rows": [{"entry": 1, "chr": 9, "kind": 0,
                                     "regions": regions}]}, DiscFixture())
        with self.assertRaisesRegex(ValueError, "regions"):
            alt.build({"rows": [{"entry": 1, "chr": 9, "kind": 0, "file": "legacy",
                                 "regions": {"japanese": "jp", "international": "usa"}}]}, DiscFixture())

    def test_separate_mod_has_only_two_global_japanese_defaults(self):
        path = ROOT / "mods-src/bag2jp.content.bag1-visuals/1.0.0/manifest.toml"
        manifest = tomllib.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["id"], "bag2jp.content.bag1-visuals")
        self.assertTrue(manifest["feature"][0]["default_enabled"])
        self.assertEqual({o["id"] for o in manifest["option"]}, {"models", "stages"})
        for option in manifest["option"]:
            self.assertEqual(option["default"], "japanese")
            self.assertEqual({c["value"] for c in option["choice"]},
                             {"japanese", "international"})

    def test_actual_vblank_routes_regions_and_restores_only_owned_offsets(self):
        source = (ROOT / "mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_versions.c").read_text()
        start = source.find("static int b1v_region_japanese")
        if start < 0:
            start = source.index("static void b1v_vblank(void)")
        block = source[start:source.index("static int b1v_active;")]
        harness = r'''
#include <stdint.h>
#include <string.h>
#include <assert.h>
#include <stdarg.h>
#define B1V_TABLE 0
#define B1V_MAGIC 0x5F324644u
/* ACTUAL_INDEX_TYPE */
static const B1AltEntry b1_alt_entries[] = {
 {0,9,0,100,10,200,20,300,30}, {1,9,3,400,40,500,50,600,60},
 {2,1,1,700,70,800,80,0,0}};
static uint32_t ram[8]={B1V_MAGIC,3,100,10,400,40,700,70}, b1v_frame;
static const char *models="japanese", *stages="japanese";
static int wanted=1;
static uint32_t psx_mod_read_word(uint32_t a){return ram[a/4];}
static void psx_mod_write_word(uint32_t a,uint32_t v){ram[a/4]=v;}
int psx_mod_option_value(const char*p,const char*f,const char*o,char*v,uint32_t n){
 assert(!strcmp(p,"bag2jp.content.bag1-visuals") && !strcmp(f,"regional"));
 const char *s=!strcmp(o,"stages")?stages:models;
 if(!s)return 0;
 if(n){strncpy(v,s,n-1);v[n-1]=0;}return 1;}
static int b1v_wanted(const B1AltEntry*e){(void)e;return wanted;}
static void b1v_model_region(void){} static void b1v_dancer_scale(void){}
static void bag2jp_strike_bag1_tick(uint32_t f){(void)f;}
static void bag2jp_heat_flame_tick(uint32_t f){(void)f;}
static void b1v_log(const char*f,...){(void)f;}
'''
        index = (ROOT / "mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_alt_index.h").read_text()
        index_type = index[index.index("typedef struct"):index.index("static const B1AltEntry")]
        harness = harness.replace("/* ACTUAL_INDEX_TYPE */", index_type)
        scenario = r'''
int main(void){
 b1v_vblank(); assert(ram[2]==300 && ram[3]==30 && ram[4]==600 && ram[5]==60);
 assert(ram[6]==700 && ram[7]==70); /* No mislabeled USA fallback for missing JP. */
 models="international"; b1v_vblank(); assert(ram[2]==200 && ram[3]==20 && ram[4]==600);
 stages="international"; b1v_vblank(); assert(ram[4]==500 && ram[5]==50 && ram[6]==800);
 models="japanese"; stages="international"; b1v_vblank(); assert(ram[2]==300 && ram[4]==500);
 wanted=0; b1v_vblank(); assert(ram[2]==100 && ram[3]==10 && ram[4]==400 && ram[6]==700);
 ram[2]=999; ram[3]=99; wanted=1; b1v_vblank(); assert(ram[2]==999 && ram[3]==99);
 ram[2]=100; models=0; stages="invalid"; b1v_vblank(); assert(ram[2]==300 && ram[4]==600);
 ram[1]=1; ram[4]=400; ram[5]=40; b1v_vblank(); assert(ram[4]==400 && ram[5]==40);
 ram[0]=0; ram[2]=100; b1v_vblank(); assert(ram[2]==100);
 return 0;}
'''
        with tempfile.TemporaryDirectory(dir=ROOT / "_work") as directory:
            c_file = Path(directory) / "visual.c"
            c_file.write_text(harness + block + scenario, encoding="utf-8")
            linux = "/mnt/" + directory[0].lower() + directory[2:].replace("\\", "/")
            subprocess.run(["wsl.exe", "-d", "Ubuntu", "--exec", "gcc", "-std=c11",
                            "-Wall", "-Werror", linux + "/visual.c", "-o", linux + "/visual"], check=True)
            subprocess.run(["wsl.exe", "-d", "Ubuntu", "--exec", linux + "/visual"], check=True)


if __name__ == "__main__":
    unittest.main()
