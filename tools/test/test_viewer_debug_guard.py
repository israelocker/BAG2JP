from pathlib import Path
import subprocess,json
root=Path(__file__).resolve().parents[2];w=root/'_work/animation-policy';w.mkdir(parents=True,exist_ok=True)
s=(root/'mods-src/bag2jp.debug.anim-trace/bag2jp_anim_trace.c').read_text();block=s[s.index('    /* Test-only native viewer access;'):s.index('    if (s_skill == -1)')]
source='''#include <stdint.h>
#include <stdlib.h>
#include <assert.h>
static int s_on,valid,flag,writes;
uint32_t psx_mod_read_word(uint32_t a){return valid?(a==0x8004E2D8u?0x54535542u:0x4D5F415Fu):0;}
uint8_t psx_mod_read_byte(uint32_t a){return (uint8_t)flag;}
void psx_mod_write_byte(uint32_t a,uint8_t value){assert(a>=0x8004E2F7u&&a<0x8004E305u);assert(value==1);writes++;}
void tick(void){
'''+block+'''}
int main(int n,char**args){s_on=atoi(args[1]);valid=atoi(args[2]);flag=atoi(args[3]);tick();tick();assert(writes==atoi(args[4]));return 0;}
'''
(w/'viewer_guard_test.c').write_text(source,newline='\n')
prefix=['wsl.exe','-d','Ubuntu','--exec']
wsl_root='/mnt/'+root.drive[0].lower()+'/'+root.as_posix()[3:]
source_path=wsl_root+'/_work/animation-policy/viewer_guard_test.c'
binary_path=wsl_root+'/_work/animation-policy/viewer_guard_test'
subprocess.run(prefix+['gcc',source_path,'-o',binary_path],check=True)
cases=[('0',1,1,0,2),('13',1,1,0,2),('14',1,1,0,0),('-1',1,1,0,0),('0junk',1,1,0,0),('',1,1,0,0),('0',0,1,0,0),('0',1,0,0,0),('0',1,1,1,0)]
for value,on,valid,flag,count in cases:
    subprocess.run(prefix+['env','BAG2JP_TEST_DANCE_VIEW_CHAR='+value,binary_path,str(on),str(valid),str(flag),str(count)],check=True)
(w/'viewer-guard-tests.json').write_text(json.dumps({'cases':cases,'passed':len(cases)},indent=2))
print('PASS:',len(cases),'actual C debug-option guard cases')
