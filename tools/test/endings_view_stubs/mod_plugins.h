#pragma once
#include "cpu_state.h"
#include <stdint.h>
#define PSX_MOD_CONSTRUCTOR(name) static void name(void)
uint32_t psx_mod_read_word(uint32_t address);
uint16_t psx_mod_read_half(uint32_t address);
uint8_t psx_mod_read_byte(uint32_t address);
void psx_mod_write_word(uint32_t address, uint32_t value);
void psx_mod_write_half(uint32_t address, uint16_t value);
void psx_mod_write_byte(uint32_t address, uint8_t value);
void psx_mod_write_code_word(uint32_t address, uint32_t value);
uint32_t psx_mod_call_guest(struct CPUState*, uint32_t, uint32_t, uint32_t, uint32_t, uint32_t, uint32_t);
int psx_mod_register_activation_plugin(const char*, void (*)(void));
int psx_mod_register_session_reset_plugin(const char*, void (*)(void));
int psx_mod_register_vblank_plugin(const char*, void (*)(void));
int psx_mod_register_guest_function_plugin(const char*, uint32_t, void (*)(struct CPUState*, uint32_t));
int psx_mod_register_instruction_plugin(const char*, uint32_t, uint32_t, void (*)(struct CPUState*, uint32_t));
int psx_mod_current_resource_path(const char*, char*, uint32_t);
