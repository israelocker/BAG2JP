/* Trace-only, one-shot observation of the JP main's SystemError arguments.
 * The generated entry has no plugin hook. An equivalent ORI in place of
 * ADDIU (both set t2=0xA0 in one cycle) routes this tiny function through the
 * interpreter's instruction hook. Restore the original word BEFORE continuing;
 * never change CPU registers, skip the error, or alter sound allocation.
 */
#ifndef BAG2JP_SYSTEM_ERROR_PROBE_H
#define BAG2JP_SYSTEM_ERROR_PROBE_H

#define BAG2_SYSTEM_ERROR_PC       0x80049F94u
#define BAG2_SYSTEM_ERROR_ORIGINAL 0x240A00A0u
#define BAG2_SYSTEM_ERROR_OBSERVED 0x340A00A0u

static int bag2_system_error_probe_state;

static void bag2_system_error_probe_arm(int enabled, FILE* log) {
    if (!enabled || !log || bag2_system_error_probe_state) return;
    if (psx_mod_read_word(BAG2_SYSTEM_ERROR_PC) != BAG2_SYSTEM_ERROR_ORIGINAL ||
        psx_mod_read_word(BAG2_SYSTEM_ERROR_PC + 4u) != 0x01400008u || /* jr t2 */
        psx_mod_read_word(BAG2_SYSTEM_ERROR_PC + 8u) != 0x240900A1u) return;
    psx_mod_write_code_word(BAG2_SYSTEM_ERROR_PC, BAG2_SYSTEM_ERROR_OBSERVED);
    bag2_system_error_probe_state = 1;
    fputs("system-error probe armed: equivalent instruction; error path unchanged\n", log);
    fflush(log);
}

static void bag2_system_error_probe_observe(struct CPUState* cpu, uint32_t address, FILE* log) {
    if (!cpu || !log || address != BAG2_SYSTEM_ERROR_PC ||
        bag2_system_error_probe_state != 1 ||
        psx_mod_read_word(address) != BAG2_SYSTEM_ERROR_OBSERVED) return;
    fprintf(log, "system-error: a0=%08X a1=%08X ra=%08X sp=%08X\n",
            cpu->gpr[4], cpu->gpr[5], cpu->gpr[31], cpu->gpr[29]);
    fflush(log);
    psx_mod_write_code_word(address, BAG2_SYSTEM_ERROR_ORIGINAL);
    bag2_system_error_probe_state = 2;
}

#endif
