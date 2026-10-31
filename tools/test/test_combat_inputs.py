"""Verify native-watch parsing and the phase gate used by the real-input test driver."""
from pathlib import Path
import tempfile,unittest,sys
sys.path.insert(0,str(Path(__file__).parent))
from combat_inputs import read_watch,is_combat,trace_rows
class CombatInputTests(unittest.TestCase):
    def test_native_combat_phase_is_hex_13(self):
        state={'8005D2C4':2,'8005D3D4':0x13,'8005E65A':3}
        self.assertTrue(is_combat(state))
        for key,value in [('8005D2C4',1),('8005D3D4',13),('8005E65A',0)]:
            self.assertFalse(is_combat({**state,key:value}))
    def test_incomplete_watch_line_cannot_replace_complete_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'watch.log';line=' '.join(f'{0x80000000+i:08X}=13' for i in range(16))
            path.write_text('f001 '+line+'\n'+'f002 '+line.replace('=13','=FF'))
            self.assertEqual(read_watch(path)['80000000'],0x13)
    def test_incomplete_watch_contract_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'watch.log';path.write_text('f001 80000000=13\n')
            self.assertEqual(read_watch(path),{})
    def test_one_frame_defense_request_survives_later_idle(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'trace.log';path.write_text('f021867 mode2 phase 1/3/3 fever0 | P1 ch0 anim76 req171 | P2 ch0 anim0 req0\nf021868 mode2 phase 1/3/3 fever0 | P1 ch0 anim76 req65535 | P2 ch0 anim0 req65535\n')
            rows=trace_rows(path)
            self.assertEqual(rows[0],(21867,76,171,0,0));self.assertEqual(len(rows),2)
if __name__=='__main__':unittest.main()
