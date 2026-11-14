"""Host execution of the production audio callbacks; clocks are the only time mocks."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def linux(path: Path) -> str:
    """Translate Windows paths for the recorded WSL GCC runner."""
    return '/mnt/' + path.drive[0].lower() + path.as_posix()[2:]


class AudioClockProbeTest(unittest.TestCase):
    def test_real_audio_callbacks_keep_legacy_sync_and_log_counter_sample_pairs(self) -> None:
        source = (ROOT / 'mods-src/bag2jp.debug.anim-trace/bag2jp_anim_trace.c').read_text()
        block = source[source.index('/* ---- audio recorder ---- */'):source.index('static void at_vblank(')]
        harness = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
static uint64_t ticks = 123456789;
static const char* SDL_GetBasePath(void) { return ""; }
static uint64_t SDL_GetPerformanceCounter(void) { return ticks; }
static uint64_t SDL_GetPerformanceFrequency(void) { return 10000000; }
'''
        scenario = r'''
int main(void) {
    int16_t pcm[1470] = {0};
    for (int i=1; i<=12; ++i) {
        if (i==12) ticks += 3430000; /* producer pause, sample count still continuous */
        audio_vblank(); at_pcm(pcm,735); ticks += 166667;
    }
    return 0;
}
'''
        with tempfile.TemporaryDirectory(dir=ROOT / '_work') as temporary:
            folder = Path(temporary)
            path = folder / 'audio.c'
            path.write_text(harness + block + scenario)
            compiled = subprocess.run(['wsl.exe','-d','Ubuntu','--exec','gcc','-std=c11',
                                       '-Wall','-Werror','-Wno-unused-function',linux(path),
                                       '-o',linux(folder/'audio')], capture_output=True, text=True)
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            result = subprocess.run(['wsl.exe','-d','Ubuntu','--cd',linux(folder),'--exec',
                                     'env','BAG2JP_AUDIO_DUMP=1',linux(folder/'audio')], capture_output=True)
            self.assertEqual(result.returncode, 0)
            legacy = (folder / 'bag2jp_audio_sync.log').read_text().splitlines()
            self.assertEqual(legacy, [f'{f} {(f-1)*735}' for f in range(1,13)])
            probe = folder / 'bag2jp_clock_probe.csv'
            self.assertTrue(probe.exists(), 'producer must retain its own high-resolution clock')
            self.assertEqual(probe.read_text().splitlines(), [
                'frame,samples,producer_ticks,producer_hz',
                '6,3675,124290124,10000000', '12,8085,128720126,10000000'])
            # Probe open failure must not break legacy PCM/sync output.
            failed = folder / 'probe-denied'; failed.mkdir()
            (failed / 'bag2jp_clock_probe.csv').mkdir()
            result = subprocess.run(['wsl.exe','-d','Ubuntu','--cd',linux(failed),'--exec',
                                     'env','BAG2JP_AUDIO_DUMP=1',linux(folder/'audio')],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertIn('audio clock probe unavailable', result.stderr)
            self.assertEqual((failed/'bag2jp_audio_sync.log').read_text().splitlines(), legacy)
            self.assertEqual((failed/'bag2jp_audio.wav').read_bytes(), (folder/'bag2jp_audio.wav').read_bytes())
            # Disabled audio dump emits neither new diagnostics nor legacy files.
            disabled = folder / 'disabled'; disabled.mkdir()
            result = subprocess.run(['wsl.exe','-d','Ubuntu','--cd',linux(disabled),'--exec',
                                     'env','BAG2JP_AUDIO_DUMP=0',linux(folder/'audio')], capture_output=True)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(list(disabled.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
