"""Prepare a candidate alternate payload from one shared model-animation list; never deploy."""
import argparse,hashlib,json,tomllib,sys
from pathlib import Path
from alternate_payload import repack,ROW,BASE
from character_workflow import motion_fingerprint

def prepare(package,index_path,animation_path,entries,output):
    sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'Tools/psx-asset-tools'))
    from psxassets import containers
    package,index_path,animation_path,output=map(Path,(package,index_path,animation_path,output))
    text=(package/'manifest.toml').read_bytes();spec=tomllib.loads(text.decode('utf-8-sig'))
    overlay=next(row for row in spec['overlay'] if row.get('file')=='payload/bag1_alt.bin')
    original=(package/overlay['file']).read_bytes();old_hash=hashlib.sha256(original).hexdigest()
    if old_hash!=overlay['sha256']:raise ValueError('Preserve payload/manifest drift')
    motion_fingerprint(animation_path)
    header=index_path.read_text();animation=animation_path.read_bytes();archives={}
    for match in ROW.finditer(header):
        entry=int(match[1])
        if entry not in entries:continue
        start=int(match[6],16)-BASE;size=int(match[7])
        if start<0 or start+size>len(original):raise ValueError('Invalid archive range')
        archive=original[start:start+size];table=containers.parse_archive(archive)
        children=[archive[offset:offset+length] for offset,length in table]
        if len(children)!=2:raise ValueError('Expected mesh and animation members')
        children[1]=animation
        archives[entry]=containers.build_archive(archive[:4],children,containers.detect_alignment(table,8+8*len(table)))
    if set(archives)!=set(entries):raise ValueError('Model entry missing from alternate index')
    data,new_header,index=repack(original,header,archives)
    old_zero=hashlib.sha256(bytes(len(original))).hexdigest();new_zero=hashlib.sha256(bytes(len(data))).hexdigest()
    new_hash=hashlib.sha256(data).hexdigest()
    if text.count(old_hash.encode())!=1 or text.count(old_zero.encode())!=1:raise ValueError('Ambiguous overlay hashes')
    text=text.replace(old_hash.encode(),new_hash.encode()).replace(old_zero.encode(),new_zero.encode())
    output.mkdir(parents=True,exist_ok=False)
    (output/'payload').mkdir();(output/'payload/bag1_alt.bin').write_bytes(data)
    (output/'manifest.toml').write_bytes(text);(output/'bag2jp_bag1_alt_index.h').write_text(new_header,newline='\n')
    return {'sha256':new_hash,'bytes':len(data),'entries':sorted(archives),'output':str(output)}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('package','index','animations','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--entries',type=int,nargs='+',required=True)
    args=parser.parse_args()
    print(json.dumps(prepare(args.package,args.index,args.animations,args.entries,args.output)))
if __name__=='__main__':main()
