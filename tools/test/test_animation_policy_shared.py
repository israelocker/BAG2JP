"""Character-independent policy and alternate-container invariants."""
from pathlib import Path
import sys,unittest,struct
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bag1import'))
from animation_policy import native_variant,adapt_events
from alternate_payload import repack,BASE,ROW
class SharedPolicyTests(unittest.TestCase):
    def test_predecessor_matches_native_table_not_level_heuristic(self):
        records=[(19,20,29,30)]
        self.assertEqual(native_variant(19,31,records),19)
        self.assertEqual(native_variant(19,29,records),20)
    def test_repack_preserves_other_entries_and_stock_fields(self):
        header='\n'.join('{%d, 2, 0, 0x1000u, 3u, 0x%Xu, 3u}'%(entry,BASE+offset) for entry,offset in ((1,0),(2,2048)))
        payload=b'one'+bytes(2045)+b'two'+bytes(2045)
        data,index,entries=repack(payload,header,{1:b'new'*1000})
        self.assertEqual(entries[2][1],3)
        self.assertEqual(data[entries[2][0]-BASE:entries[2][0]-BASE+3],b'two')
        self.assertIn('0x1000u, 3u',index)
        changed=repack(payload,header,{1:b'not'*1000})[1]
        self.assertNotEqual(index.splitlines()[0],changed.splitlines()[0])
    def test_repack_rejects_outside_index_and_capacity(self):
        header='{1, 0, 0, 0x1000u, 3u, 0x%Xu, 3u}'%BASE
        with self.assertRaises(ValueError):repack(b'abc',header,{9:b'x'})
        with self.assertRaises(ValueError):repack(b'ab',header,{})
        with patch('alternate_payload.CAPACITY',1):
            with self.assertRaises(ValueError):repack(b'abc',header,{})
    def test_event_bounds_are_checked(self):
        data=bytearray(38);struct.pack_into('<I',data,0,28);struct.pack_into('<H',data,4,2);struct.pack_into('<I',data,28,4)
        with self.assertRaises(ValueError):adapt_events(bytes(data),{'required_events':[[1,2,902]]})
    def test_original_duplicate_events_are_preserved(self):
        data=bytearray(32);struct.pack_into('<I',data,0,28);struct.pack_into('<H',data,4,2);struct.pack_into('<I',data,28,4)
        events=struct.pack('<HHH',2,0,5)*2
        animation=bytes(data)+bytes(4)+events+bytes(2)
        from animlib import info
        self.assertEqual(info(adapt_events(animation,{}))[1],[(2,0,5),(2,0,5)])
if __name__=='__main__':unittest.main()
