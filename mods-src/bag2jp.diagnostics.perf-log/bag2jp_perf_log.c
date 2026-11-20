/* Performance log for BAG2JP (always on, read-only).
 *
 * Writes <exe dir>/bag2jp_perf.log on every launch (the previous run is kept as
 * bag2jp_perf.prev.log) so a player on another PC can send it back:
 *   - header: OS build, CPU brand/cores, RAM, GPUs and driver key, monitor mode,
 *     and the video lines of settings.toml (renderer, vsync, threads);
 *   - one line per second: guest VSync count delta (60 = full speed, lower means
 *     the host cannot emulate in real time), process CPU % (of whole machine and
 *     of one core), system CPU %, working set, system free RAM, process GPU 3D %
 *     (PDH, when the driver exposes it) and the worst sampling gap;
 *   - a summary at exit: seconds below 57 vblank/s and the slowest second.
 *
 * Runs on its own thread; it only reads guest RAM (libetc VSync counter
 * 0x800573F0, BAG2 root 0x8005D3D4) and never writes it. */
#include "mod_plugins.h"

#include <windows.h>
#include <psapi.h>
#include <intrin.h>
#include <stdlib.h>
#include <wchar.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define PL_VSYNC_COUNTER 0x800573F0u
#define PL_ROOT          0x8005D3D4u
#define PL_SLOW_VBLANKS  57u

static FILE* s_log;
static volatile LONG s_stop;
static uint32_t s_seconds, s_slow_seconds, s_worst_vblanks = 0xFFFFFFFFu, s_worst_at;

/* ---- PDH (loaded dynamically: pdh.dll is optional) ---- */
typedef LONG (WINAPI *PdhOpenQueryW_t)(LPCWSTR, DWORD_PTR, HANDLE*);
typedef LONG (WINAPI *PdhAddEnglishCounterW_t)(HANDLE, LPCWSTR, DWORD_PTR, HANDLE*);
typedef LONG (WINAPI *PdhCollectQueryData_t)(HANDLE);
typedef LONG (WINAPI *PdhGetFormattedCounterArrayW_t)(HANDLE, DWORD, DWORD*, DWORD*, void*);
typedef struct { LPWSTR name; struct { DWORD status; DWORD pad; double value; } fmt; } PlPdhItem;
static PdhCollectQueryData_t p_collect;
static PdhGetFormattedCounterArrayW_t p_array;
static HANDLE s_query, s_gpu_counter;

static void pl_gpu_open(void) {
    HMODULE pdh = LoadLibraryA("pdh.dll");
    if (!pdh) return;
    PdhOpenQueryW_t open = (PdhOpenQueryW_t)(void*)GetProcAddress(pdh, "PdhOpenQueryW");
    PdhAddEnglishCounterW_t add = (PdhAddEnglishCounterW_t)(void*)GetProcAddress(pdh, "PdhAddEnglishCounterW");
    p_collect = (PdhCollectQueryData_t)(void*)GetProcAddress(pdh, "PdhCollectQueryData");
    p_array = (PdhGetFormattedCounterArrayW_t)(void*)GetProcAddress(pdh, "PdhGetFormattedCounterArrayW");
    if (!open || !add || !p_collect || !p_array || open(NULL, 0, &s_query) != 0) { p_collect = NULL; return; }
    wchar_t path[128];
    swprintf(path, 128, L"\\GPU Engine(pid_%lu_*engtype_3D)\\Utilization Percentage", GetCurrentProcessId());
    if (add(s_query, path, 0, &s_gpu_counter) != 0) { p_collect = NULL; return; }
    p_collect(s_query);
}

/* Sum of this process' 3D engine utilisation, or -1 when unavailable. */
static double pl_gpu_sample(void) {
    if (!p_collect || p_collect(s_query) != 0) return -1.0;
    DWORD bytes = 0, count = 0;
    if (p_array(s_gpu_counter, 0x200 /* PDH_FMT_DOUBLE */, &bytes, &count, NULL) != (LONG)0x800007D2 || !bytes)
        return -1.0;
    PlPdhItem* items = (PlPdhItem*)malloc(bytes);
    double sum = -1.0;
    if (items && p_array(s_gpu_counter, 0x200, &bytes, &count, items) == 0) {
        sum = 0.0;
        for (DWORD i = 0; i < count; ++i) if (items[i].fmt.status == 0) sum += items[i].fmt.value;
    }
    free(items);
    return sum;
}

/* ---- static header ---- */
static void pl_header(void) {
    SYSTEMTIME t; GetLocalTime(&t);
    fprintf(s_log, "BAG2JP perf log %04u-%02u-%02u %02u:%02u:%02u\n",
            t.wYear, t.wMonth, t.wDay, t.wHour, t.wMinute, t.wSecond);

    typedef LONG (WINAPI *RtlGetVersion_t)(OSVERSIONINFOW*);
    RtlGetVersion_t rgv = (RtlGetVersion_t)(void*)GetProcAddress(GetModuleHandleA("ntdll.dll"), "RtlGetVersion");
    OSVERSIONINFOW os = { sizeof os };
    if (rgv && rgv(&os) == 0)
        fprintf(s_log, "os: Windows %lu.%lu build %lu\n", os.dwMajorVersion, os.dwMinorVersion, os.dwBuildNumber);

    int r[4]; char brand[49] = {0};
    __cpuid(r, 0x80000000);
    if ((unsigned)r[0] >= 0x80000004u)
        for (int i = 0; i < 3; ++i) { __cpuid(r, 0x80000002 + i); memcpy(brand + 16 * i, r, 16); }
    SYSTEM_INFO si; GetSystemInfo(&si);
    fprintf(s_log, "cpu: %s | logical cores %lu\n", brand[0] ? brand : "unknown", si.dwNumberOfProcessors);

    MEMORYSTATUSEX m = { sizeof m };
    if (GlobalMemoryStatusEx(&m))
        fprintf(s_log, "ram: %llu MB total, %llu MB free at start\n",
                m.ullTotalPhys >> 20, m.ullAvailPhys >> 20);

    DISPLAY_DEVICEA d = { sizeof d };
    for (DWORD i = 0; EnumDisplayDevicesA(NULL, i, &d, 0); ++i, d.cb = sizeof d)
        fprintf(s_log, "gpu: %s%s%s\n", d.DeviceString,
                (d.StateFlags & DISPLAY_DEVICE_PRIMARY_DEVICE) ? " (primary)" : "",
                (d.StateFlags & DISPLAY_DEVICE_ATTACHED_TO_DESKTOP) ? "" : " (inactive)");
    DEVMODEA dm = { .dmSize = sizeof dm };
    if (EnumDisplaySettingsA(NULL, ENUM_CURRENT_SETTINGS, &dm))
        fprintf(s_log, "monitor: %lux%lu @ %lu Hz\n", dm.dmPelsWidth, dm.dmPelsHeight, dm.dmDisplayFrequency);

    static const char* keys[] = { "renderer", "vsync", "render_thread", "present_thread",
                                  "fullscreen", "internal_resolution", "resolution_scale" };
    for (int f = 0; f < 2; ++f) {
        const char* name = f ? "game.toml" : "settings.toml";
        FILE* in = fopen(name, "r");
        if (!in) { fprintf(s_log, "%s: missing\n", name); continue; }
        char line[256];
        while (fgets(line, sizeof line, in)) {
            const char* p = line; while (*p == ' ' || *p == '\t') ++p;
            for (size_t k = 0; k < sizeof keys / sizeof *keys; ++k)
                if (!strncmp(p, keys[k], strlen(keys[k]))) { fprintf(s_log, "%s: %s", name, p); break; }
        }
        fclose(in);
    }
    fprintf(s_log, "columns: t vbl/s root proc_cpu%%(machine) proc_cpu%%(1core) sys_cpu%% ws_MB free_MB gpu3d%% gap_ms\n");
    fflush(s_log);
}

static uint64_t ft64(FILETIME f) { return ((uint64_t)f.dwHighDateTime << 32) | f.dwLowDateTime; }

static DWORD WINAPI pl_thread(LPVOID unused) {
    (void)unused;
    pl_gpu_open();
    SYSTEM_INFO si; GetSystemInfo(&si);
    const double cores = si.dwNumberOfProcessors ? si.dwNumberOfProcessors : 1;
    HANDLE self = GetCurrentProcess();
    FILETIME a, b, k, u, si_idle, si_k, si_u;
    GetProcessTimes(self, &a, &b, &k, &u);
    GetSystemTimes(&si_idle, &si_k, &si_u);
    uint64_t last_proc = ft64(k) + ft64(u), last_idle = ft64(si_idle), last_sys = ft64(si_k) + ft64(si_u);
    uint32_t last_vbl = psx_mod_read_word(PL_VSYNC_COUNTER);
    LARGE_INTEGER freq, prev, now; QueryPerformanceFrequency(&freq); QueryPerformanceCounter(&prev);
    double worst_gap = 0.0;

    while (!s_stop) {
        /* 1 s window built from 100 ms ticks so the worst host stall shows up too. */
        for (int i = 0; i < 10 && !s_stop; ++i) {
            Sleep(100);
            QueryPerformanceCounter(&now);
            double gap = (double)(now.QuadPart - prev.QuadPart) * 1000.0 / (double)freq.QuadPart;
            if (gap > worst_gap) worst_gap = gap;
            prev = now;
        }
        GetProcessTimes(self, &a, &b, &k, &u);
        GetSystemTimes(&si_idle, &si_k, &si_u);
        uint64_t proc = ft64(k) + ft64(u), idle = ft64(si_idle), sys = ft64(si_k) + ft64(si_u);
        double sys_span = (double)(sys - last_sys);
        double proc_machine = sys_span > 0 ? 100.0 * (double)(proc - last_proc) / sys_span : 0.0;
        double sys_cpu = sys_span > 0 ? 100.0 * (1.0 - (double)(idle - last_idle) / sys_span) : 0.0;
        last_proc = proc; last_idle = idle; last_sys = sys;

        uint32_t vbl = psx_mod_read_word(PL_VSYNC_COUNTER), dv = vbl - last_vbl; last_vbl = vbl;
        PROCESS_MEMORY_COUNTERS pmc = { sizeof pmc };
        K32GetProcessMemoryInfo(self, &pmc, sizeof pmc);
        MEMORYSTATUSEX m = { sizeof m }; GlobalMemoryStatusEx(&m);
        double gpu = pl_gpu_sample();

        ++s_seconds;
        if (dv < PL_SLOW_VBLANKS && dv > 0) ++s_slow_seconds;
        if (dv > 0 && dv < s_worst_vblanks) { s_worst_vblanks = dv; s_worst_at = s_seconds; }
        fprintf(s_log, "%5u %3u %2X %5.1f %5.1f %5.1f %5llu %6llu %5.1f %5.0f\n", s_seconds, dv,
                psx_mod_read_word(PL_ROOT) & 0xFFu, proc_machine, proc_machine * cores, sys_cpu,
                (unsigned long long)(pmc.WorkingSetSize >> 20), m.ullAvailPhys >> 20, gpu, worst_gap);
        fflush(s_log);
        worst_gap = 0.0;
    }
    return 0;
}

static void pl_exit(void) {
    InterlockedExchange(&s_stop, 1);
    if (!s_log) return;
    fprintf(s_log, "summary: %u s logged, %u s below %u vbl/s", s_seconds, s_slow_seconds, PL_SLOW_VBLANKS);
    if (s_worst_vblanks != 0xFFFFFFFFu) fprintf(s_log, ", slowest %u vbl/s at t=%u", s_worst_vblanks, s_worst_at);
    fprintf(s_log, "\n");
    fclose(s_log); s_log = NULL;
}

PSX_MOD_CONSTRUCTOR(bag2jp_register_perf_log) {
    char dir[MAX_PATH], path[MAX_PATH + 32], prev[MAX_PATH + 32];
    DWORD n = GetModuleFileNameA(NULL, dir, MAX_PATH);
    while (n && dir[n - 1] != '\\' && dir[n - 1] != '/') --n;
    dir[n] = 0;
    snprintf(path, sizeof path, "%sbag2jp_perf.log", dir);
    snprintf(prev, sizeof prev, "%sbag2jp_perf.prev.log", dir);
    MoveFileExA(path, prev, MOVEFILE_REPLACE_EXISTING);
    s_log = fopen(path, "w");
    if (!s_log) return;
    pl_header();
    atexit(pl_exit);
    HANDLE th = CreateThread(NULL, 0, pl_thread, NULL, 0, NULL);
    if (th) { SetThreadPriority(th, THREAD_PRIORITY_BELOW_NORMAL); CloseHandle(th); }
}
