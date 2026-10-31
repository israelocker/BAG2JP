#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "bag2jp_bag1_versions.c"
extern void bag2jp_bag1_set_stage_version(int) __attribute__((weak));
static void stage_version(int v) { if (bag2jp_bag1_set_stage_version) bag2jp_bag1_set_stage_version(v); }
static int stage_select_enabled;
int bag2jp_stage_select_enabled(void) { return stage_select_enabled; }
int main(void) {
 B1AltEntry stage={.entry=200,.chr=0,.kind=3};
 B1AltEntry player={.entry=59,.chr=0,.kind=0};
 b1v_version[0][0]=1;
 stage_version(0);
 if(b1v_wanted(&stage)!=0) { fprintf(stderr,"FAIL: explicitly selected BAG2 stage still follows BAG1 character\n");return 1; }
 assert(b1v_wanted(&player)==1);
 b1v_version[0][0]=0;stage_version(1);
 assert(b1v_wanted(&stage)==1);assert(b1v_wanted(&player)==0);
 b1v_force_stock=1;assert(b1v_wanted(&stage)==0);
 b1v_force_stock=0;stage_version(-1);assert(b1v_wanted(&stage)==0);
 b1v_version[0][0]=1;assert(b1v_wanted(&stage)==1);
 b1v_active=1;stage_select_enabled=0;uint32_t legacy=bag2jp_bag1_content_id();
 stage_select_enabled=1;assert(bag2jp_bag1_content_id()!=legacy);
 b1v_force_stock=1;assert(bag2jp_bag1_content_id()!=legacy);
 puts("PASS: independent stage choice, character unchanged, stock fallback, legacy auto and online menu identity");
}
uint32_t psx_mod_read_word(uint32_t a){return a==B1V_CHAR_P1?0:0;}
uint8_t psx_mod_read_byte(uint32_t a){(void)a;return 0;}
void psx_mod_write_word(uint32_t a,uint32_t v){(void)a;(void)v;}
int psx_mod_current_option_value(const char*a,char*b,size_t n){(void)a;(void)b;(void)n;return 0;}
