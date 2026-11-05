"""Repack existing alternate entries while preserving unrelated archives and stock metadata."""
import hashlib,re
SECTOR=2048
BASE=(224035-179)*SECTOR
CAPACITY=13500*SECTOR
ROW=re.compile(r'\{(\d+), (\d+), (\d+), 0x([0-9A-F]+)u, (\d+)u, 0x([0-9A-F]+)u, (\d+)u\}')
def repack(payload,header,replacements):
    rows=[tuple(int(value,16 if i in (3,5) else 10) for i,value in enumerate(match.groups())) for match in ROW.finditer(header)]
    if not rows or len({row[0] for row in rows})!=len(rows):raise ValueError('Invalid alternate index')
    if set(replacements)-{row[0] for row in rows}:raise ValueError('Unknown alternate entry')
    result=bytearray();updated={};shared={}
    for entry,character,kind,stock_offset,stock_size,alt_offset,alt_size in rows:
        start=alt_offset-BASE
        if start<0 or alt_size<=0 or start+alt_size>len(payload):raise ValueError('Alternate entry outside payload')
        # Entries that shared one archive stay shared unless a replacement separates them.
        if entry not in replacements and (alt_offset,alt_size) in shared:
            updated[entry]=shared[(alt_offset,alt_size)];continue
        data=replacements.get(entry,payload[start:start+alt_size])
        if not data:raise ValueError('Empty alternate archive')
        offset=BASE+len(result);result+=data
        result+=bytes((-len(result))%SECTOR)
        updated[entry]=(offset,len(data))
        if entry not in replacements:shared[(alt_offset,alt_size)]=updated[entry]
    if len(result)>CAPACITY:raise ValueError('DUMMY.BIN capacity exceeded')
    def replace(match):
        entry=int(match[1]);offset,size=updated[entry]
        return '{'+', '.join([match[1],match[2],match[3],'0x'+match[4]+'u',match[5]+'u',f'0x{offset:X}u',str(size)+'u'])+'}'
    header=ROW.sub(replace,header)
    digest=hashlib.sha256(result).hexdigest()
    header=re.sub(r'^#define B1_ALT_CONTENT_TAG.*\n','',header,flags=re.M)
    header=f'#define B1_ALT_CONTENT_TAG 0x{digest[:8].upper()}u\n'+header
    return bytes(result),header,updated
