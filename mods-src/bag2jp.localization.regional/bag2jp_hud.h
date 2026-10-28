/* BAG2JP: several title layers share the runtime's single HUD draw callback. */
#pragma once
typedef void (*Bag2jpHudFn)(int width, int height, void* ctx);
void bag2jp_hud_add(Bag2jpHudFn fn, void* ctx);   /* idempotent; draw order = add order */
