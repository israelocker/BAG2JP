#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
uint16_t psx_mod_read_half(uint32_t a);
#include "bag2jp_bag1_versions.c"
extern void bag2jp_bag1_set_stage_choice(int, int) __attribute__((weak));
extern void bag2jp_bag1_set_stage_version(int) __attribute__((weak));
static void stage_choice(int c, int v) {
  if (bag2jp_bag1_set_stage_choice) bag2jp_bag1_set_stage_choice(c, v);
  else if (bag2jp_bag1_set_stage_version && c == 0) bag2jp_bag1_set_stage_version(v);
}
static void stage_version(int v) { stage_choice(0, v); }
static int stage_select_enabled;
int bag2jp_stage_select_enabled(void) { return stage_select_enabled; }
int main(void) {
 B1AltEntry stage={.entry=200,.chr=0,.kind=3};
 B1AltEntry player={.entry=59,.chr=0,.kind=0};
 B1AltEntry strike_stage={.entry=209,.chr=1,.kind=3};
 B1AltEntry strike_player={.entry=73,.chr=1,.kind=0};
 b1v_version[0][0]=1;
 stage_version(0);
 if(b1v_wanted(&stage)!=0) { fprintf(stderr,"FAIL: explicitly selected BAG2 stage still follows BAG1 character\n");return 1; }
 assert(b1v_wanted(&player)==1);
 b1v_version[0][0]=0;stage_version(1);
 assert(b1v_wanted(&stage)==1);assert(b1v_wanted(&player)==0);
 b1v_force_stock=1;assert(b1v_wanted(&stage)==0);
 b1v_force_stock=0;stage_version(-1);assert(b1v_wanted(&stage)==0);
 b1v_version[0][0]=1;assert(b1v_wanted(&stage)==1);

 b1v_version[1][0]=1;
 stage_choice(1, 0);
 assert(b1v_wanted(&strike_stage)==0);
 assert(b1v_wanted(&strike_player)==1);
 b1v_version[1][0]=0;stage_choice(1, 1);
 assert(b1v_wanted(&strike_stage)==1);assert(b1v_wanted(&strike_player)==0);
 stage_choice(1, -1);assert(b1v_wanted(&strike_stage)==0);
 b1v_version[1][0]=1;assert(b1v_wanted(&strike_stage)==1);
 b1v_active=1;stage_select_enabled=0;uint32_t legacy=bag2jp_bag1_content_id();
 uint32_t old_id=2166136261u;const uint8_t* old_data=(const uint8_t*)b1_alt_entries;
 for(unsigned i=0;i<sizeof b1_alt_entries;++i){old_id^=old_data[i];old_id*=16777619u;}
 assert(legacy!=old_id); /* changed voice payload must reject older peers even with the same index */
 stage_select_enabled=1;assert(bag2jp_bag1_content_id()!=legacy);
 b1v_force_stock=1;assert(bag2jp_bag1_content_id()!=legacy);
 puts("PASS: independent stage choice, character unchanged, stock fallback, legacy auto and online menu identity");
}
uint32_t psx_mod_read_word(uint32_t a){return a==B1V_CHAR_P1?0:0;}
uint16_t psx_mod_read_half(uint32_t a){(void)a;return 0;}
uint8_t psx_mod_read_byte(uint32_t a){(void)a;return 0;}
void psx_mod_write_word(uint32_t a,uint32_t v){(void)a;(void)v;}
int psx_mod_current_option_value(const char*a,char*b,size_t n){(void)a;(void)b;(void)n;return 0;}
