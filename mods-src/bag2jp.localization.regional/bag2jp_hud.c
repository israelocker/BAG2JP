/* BAG2JP: one psx_host_set_hud_draw_cb owner (render thread) that calls every title layer
 * (HD intro movie, international VS screen). Each layer draws only while it is active. */
#include "bag2jp_hud.h"
#include "host_overlay.h"
#include <SDL3/SDL.h>

#define HUD_MAX 8
static struct { Bag2jpHudFn fn; void* ctx; } s_layers[HUD_MAX];
static int s_count;
static SDL_Mutex* s_lock;

static void hud_mux(int width, int height, void* ctx) {
    (void)ctx;
    if (!s_lock) return;
    SDL_LockMutex(s_lock);
    for (int i = 0; i < s_count; ++i) s_layers[i].fn(width, height, s_layers[i].ctx);
    SDL_UnlockMutex(s_lock);
}

void bag2jp_hud_add(Bag2jpHudFn fn, void* ctx) {
    if (!s_lock) s_lock = SDL_CreateMutex();
    if (!s_lock || !fn) return;
    SDL_LockMutex(s_lock);
    int found = 0;
    for (int i = 0; i < s_count; ++i) if (s_layers[i].fn == fn) { s_layers[i].ctx = ctx; found = 1; }
    if (!found && s_count < HUD_MAX) { s_layers[s_count].fn = fn; s_layers[s_count].ctx = ctx; s_count++; }
    SDL_UnlockMutex(s_lock);
    psx_host_set_hud_draw_cb(hud_mux, NULL);
}
