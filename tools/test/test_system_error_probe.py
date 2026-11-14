"""Exercise the trace-only SystemError observer with a real C CPU snapshot."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class SystemErrorProbeTest(unittest.TestCase):
    def test_observer_guards_restores_instruction_and_preserves_cpu(self):
        header = ROOT / 'mods-src/bag2jp.debug.anim-trace/bag2jp_system_error_probe.h'
        self.assertTrue(header.exists(), 'SystemError observer is not implemented')
        harness = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef struct CPUState {uint32_t gpr[32],pc,hi,lo;} CPUState;
static uint32_t word=0x240A00A0u, writes;
static uint32_t psx_mod_read_word(uint32_t a){
 if(a==0x80049F98u)return 0x01400008u;
 if(a==0x80049F9Cu)return 0x240900A1u;
 assert(a==0x80049F94u);return word;}
static void psx_mod_write_code_word(uint32_t a,uint32_t v){assert(a==0x80049F94u);word=v;++writes;}
/* HEADER */
int main(void){
 FILE *log=tmpfile(); assert(log);
 bag2_system_error_probe_arm(0,log); assert(writes==0);
 word=123; bag2_system_error_probe_arm(1,log); assert(word==123 && writes==0);
 word=BAG2_SYSTEM_ERROR_ORIGINAL;
 bag2_system_error_probe_arm(1,log);
 assert(word==BAG2_SYSTEM_ERROR_OBSERVED && writes==1);
 bag2_system_error_probe_arm(1,log); assert(writes==1);
 CPUState cpu={0}; cpu.gpr[4]='V'; cpu.gpr[5]=1;
 cpu.gpr[31]=0x8002E060u; cpu.gpr[29]=0x807FFEA0u; cpu.pc=0x80049F94u;
 CPUState before=cpu;
 bag2_system_error_probe_observe(&cpu,0x80049F90u,log); assert(writes==1);
 bag2_system_error_probe_observe(&cpu,0x80049F94u,log);
 assert(memcmp(&before,&cpu,sizeof cpu)==0);
 assert(word==BAG2_SYSTEM_ERROR_ORIGINAL && writes==2);
 bag2_system_error_probe_arm(1,log); assert(writes==2); /* One-shot. */
 rewind(log); char text[1024]={0}; fread(text,1,sizeof text-1,log);
 assert(strstr(text,"system-error: a0=00000056 a1=00000001 ra=8002E060 sp=807FFEA0"));
 fclose(log); return 0;
}
'''.replace('/* HEADER */', header.read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory(dir=ROOT / '_work') as directory:
            path = Path(directory)
            (path / 'probe.c').write_text(harness, encoding='utf-8')
            linux = '/mnt/' + directory[0].lower() + directory[2:].replace('\\', '/')
            subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11',
                            '-Wall', '-Werror', linux+'/probe.c', '-o', linux+'/probe'], check=True)
            subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', linux+'/probe'], check=True)


if __name__ == '__main__':
    unittest.main()
