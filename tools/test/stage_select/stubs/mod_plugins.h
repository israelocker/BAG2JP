#pragma once
#include <stdint.h>
#include <stddef.h>
uint32_t psx_mod_read_word(uint32_t);
uint8_t psx_mod_read_byte(uint32_t);
void psx_mod_write_word(uint32_t,uint32_t);
int psx_mod_current_option_value(const char*,char*,size_t);
#define PSX_MOD_CONSTRUCTOR(name) static void name(void)
static inline int psx_mod_register_vblank_plugin(const char*a,void(*b)(void)){(void)a;(void)b;return 1;}
static inline int psx_mod_register_activation_plugin(const char*a,void(*b)(void)){(void)a;(void)b;return 1;}
static inline int psx_mod_register_session_reset_plugin(const char*a,void(*b)(void)){(void)a;(void)b;return 1;}
static inline int psx_mod_register_option_changed_plugin(const char*a,int(*b)(const char*,const char*)){(void)a;(void)b;return 1;}
