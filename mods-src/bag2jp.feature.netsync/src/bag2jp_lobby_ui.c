#include "bag2jp_lobby_ui.h"
#include "bag2jp_lobby_client.h"
#include "host_osd.h"
#include "host_overlay.h"

#include <SDL3/SDL.h>
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <windows.h>
#include <GL/gl.h>
#endif

extern void bag2jp_netsync_apply_lobby_match(const char* room_code);
extern void bag2jp_netsync_disconnect_lobby(void);

typedef enum {
    UI_CLOSED = 0,
    UI_LOBBY = 1,
    UI_ROOM = 2
} LobbyUiMode;

typedef struct {
    const char* name;
    float r, g, b;
    float acc_r, acc_g, acc_b;
} Bag2AvatarInfo;

static const Bag2AvatarInfo s_avatars[] = {
    { "HEAT",     0.85f, 0.16f, 0.14f, 0.98f, 0.78f, 0.12f },
    { "HIRO",     0.18f, 0.36f, 0.85f, 0.96f, 0.96f, 0.98f },
    { "KITTY-N",  0.92f, 0.28f, 0.62f, 0.98f, 0.88f, 0.25f },
    { "KELLY",    0.16f, 0.62f, 0.88f, 0.98f, 0.68f, 0.82f },
    { "STRIKE",   0.22f, 0.52f, 0.28f, 0.94f, 0.82f, 0.22f },
    { "TSUTOMU",  0.88f, 0.45f, 0.12f, 0.24f, 0.72f, 0.92f },
    { "SHORTY",   0.95f, 0.52f, 0.72f, 0.98f, 0.92f, 0.32f },
    { "GAS-O",    0.38f, 0.68f, 0.22f, 0.78f, 0.24f, 0.78f },
    { "COMET",    0.45f, 0.32f, 0.86f, 0.32f, 0.92f, 0.88f },
    { "CAPOEIRA", 0.14f, 0.72f, 0.52f, 0.98f, 0.86f, 0.16f },
    { "ROBO-Z",   0.78f, 0.64f, 0.16f, 0.88f, 0.22f, 0.18f },
    { "PANDER",   0.22f, 0.22f, 0.26f, 0.96f, 0.96f, 0.98f }
};
#define BAG2_AVATAR_COUNT ((int)(sizeof(s_avatars) / sizeof(s_avatars[0])))

static LobbyUiMode s_mode = UI_CLOSED;
static int s_selected_room = 0;
static int s_local_ready = 0;
static int s_editing_name = 0;
static char s_chat_input[128] = {0};
static int s_chat_len = 0;
static char s_player_name[32] = "Player";
static int s_player_avatar = 0;
static char s_server_host[64] = "127.0.0.1";
static uint16_t s_server_port = 47400;
static uint8_t s_prev_keys[256] = {0};

/* P1: Fade-to-black transition state (14 frames out + 14 frames in at 60fps) */
static int s_fade_phase = 0; /* 0=none, 1=out, 2=in */
static int s_fade_step = 0;  /* 0..14 */
static LobbyUiMode s_fade_target = UI_CLOSED;
static int s_frame_counter = 0;

/* P2/P3: SFX & Visual feedback state */
static int s_prev_chat_count = 0;
static int s_prev_guest_ready = 0;
static char s_prev_error[128] = {0};
static char s_banner_text[96] = {0};
static int s_banner_frames = 0;

/* P4: Dynamic XInput gamepad state + SDL3 per-window input sink queue */
static uint16_t s_prev_pad = 0;
static uint8_t s_sink_vk[256] = {0};
static uint8_t s_frame_vk[256] = {0};

static int sdl_key_to_vk(SDL_Keycode k) {
    if (k >= 'a' && k <= 'z') return (int)(k - 'a' + 'A');
    if (k >= 'A' && k <= 'Z') return (int)k;
    if (k >= '0' && k <= '9') return (int)k;
    switch (k) {
        case SDLK_RETURN:    return 0x0D;
        case SDLK_ESCAPE:    return 0x1B;
        case SDLK_BACKSPACE: return 0x08;
        case SDLK_SPACE:     return 0x20;
        case SDLK_LEFT:      return 0x25;
        case SDLK_UP:        return 0x26;
        case SDLK_RIGHT:     return 0x27;
        case SDLK_DOWN:      return 0x28;
        case SDLK_F4:        return 0x73;
        case SDLK_F5:        return 0x74;
        case SDLK_F6:        return 0x75;
        case SDLK_F7:        return 0x76;
        case SDLK_F9:        return 0x78;
        default:             return 0;
    }
}

static int lobby_input_sink(const void* ev_ptr, void* ctx) {
    (void)ctx;
    if (!ev_ptr) return 0;
    const SDL_Event* ev = (const SDL_Event*)ev_ptr;
    if (ev->type == SDL_EVENT_KEY_DOWN && !ev->key.repeat) {
        int vk = sdl_key_to_vk(ev->key.key);
        if (vk == 0x78) { /* F9: allow toggling Lobby on any window regardless of focus */
            s_sink_vk[vk] = 1;
            return 1;
        }
        if (s_mode == UI_CLOSED) return 0;
        if (vk > 0 && vk < 256) {
            s_sink_vk[vk] = 1;
        }
        return 1; /* consume while Lobby/Room is open */
    }
    if (ev->type == SDL_EVENT_GAMEPAD_BUTTON_DOWN && s_mode != UI_CLOSED) {
        int vk = 0;
        switch (ev->gbutton.button) {
            case SDL_GAMEPAD_BUTTON_DPAD_UP:        vk = VK_UP; break;
            case SDL_GAMEPAD_BUTTON_DPAD_DOWN:      vk = VK_DOWN; break;
            case SDL_GAMEPAD_BUTTON_DPAD_LEFT:      vk = VK_LEFT; break;
            case SDL_GAMEPAD_BUTTON_DPAD_RIGHT:     vk = VK_RIGHT; break;
            case SDL_GAMEPAD_BUTTON_SOUTH:          vk = VK_RETURN; break;
            case SDL_GAMEPAD_BUTTON_EAST:           vk = VK_ESCAPE; break;
            case SDL_GAMEPAD_BUTTON_WEST:           vk = (s_mode == UI_LOBBY) ? 'C' : VK_F5; break;
            case SDL_GAMEPAD_BUTTON_NORTH:          vk = (s_mode == UI_LOBBY) ? 'R' : VK_F4; break;
            case SDL_GAMEPAD_BUTTON_LEFT_SHOULDER:
            case SDL_GAMEPAD_BUTTON_RIGHT_SHOULDER: vk = (s_mode == UI_LOBBY) ? 'P' : VK_F4; break;
            case SDL_GAMEPAD_BUTTON_START:          vk = (s_mode == UI_ROOM && bag2jp_lobby_state()->is_host) ? VK_F6 : VK_F5; break;
            case SDL_GAMEPAD_BUTTON_BACK:           vk = (s_mode == UI_ROOM && bag2jp_lobby_state()->is_host) ? VK_F7 : 0; break;
            default: break;
        }
        if (vk > 0 && vk < 256) s_sink_vk[vk] = 1;
        return 1;
    }
    return 0;
}

/* P2: Native PS1 SPU SFX queue (drained on guest CPU thread via FUN_8002e478) */
static volatile uint32_t s_pending_sfx = 0;
static volatile int s_pending_start_2p = 0;
static int s_in_online_match = 0;

uint32_t bag2jp_lobby_pop_sfx(void) {
    uint32_t id = s_pending_sfx;
    if (id != 0u) s_pending_sfx = 0u;
    return id;
}

int bag2jp_lobby_pop_start_2p(void) {
    int v = s_pending_start_2p;
    if (v != 0) s_pending_start_2p = 0;
    return v;
}

static void play_ui_sfx(const char* wav_name) {
    if (!wav_name) return;
    if (strcmp(wav_name, "sfx_cursor.wav") == 0)       s_pending_sfx = 0x200u;
    else if (strcmp(wav_name, "sfx_confirm.wav") == 0) s_pending_sfx = 0x201u;
    else if (strcmp(wav_name, "sfx_cancel.wav") == 0)  s_pending_sfx = 0x202u;
    else if (strcmp(wav_name, "sfx_error.wav") == 0)   s_pending_sfx = 0x203u;
    else if (strcmp(wav_name, "sfx_ready.wav") == 0)   s_pending_sfx = 0x201u;
    else if (strcmp(wav_name, "sfx_chat.wav") == 0)    s_pending_sfx = 0x200u;
}

#ifdef _WIN32

typedef struct {
    DWORD dwPacketNumber;
    WORD  wButtons;
    BYTE  bLeftTrigger;
    BYTE  bRightTrigger;
    SHORT sThumbLX;
    SHORT sThumbLY;
    SHORT sThumbRX;
    SHORT sThumbRY;
} Bag2XInputState;
typedef DWORD (WINAPI *PFN_XInputGetState)(DWORD, Bag2XInputState*);
static PFN_XInputGetState p_XInputGetState = NULL;
static int s_xinput_init = 0;

static uint16_t poll_gamepad_edges(void) {
    if (!s_xinput_init) {
        s_xinput_init = 1;
        HMODULE hm = LoadLibraryA("xinput1_4.dll");
        if (!hm) hm = LoadLibraryA("xinput9_1_0.dll");
        if (hm) p_XInputGetState = (PFN_XInputGetState)GetProcAddress(hm, "XInputGetState");
    }
    if (!p_XInputGetState) return 0;
    DWORD fg_pid = 0;
    HWND fg = GetForegroundWindow();
    if (fg) GetWindowThreadProcessId(fg, &fg_pid);
    if (fg_pid != GetCurrentProcessId()) { s_prev_pad = 0; return 0; }
    Bag2XInputState xs;
    if (p_XInputGetState(0, &xs) != 0) { s_prev_pad = 0; return 0; }
    uint16_t cur = (uint16_t)xs.wButtons;
    uint16_t edges = (uint16_t)(cur & ~s_prev_pad);
    s_prev_pad = cur;
    return edges;
}
#else
static uint16_t poll_gamepad_edges(void) { return 0; }
#endif

static void show_banner(const char* msg) {
    if (!msg || !msg[0]) return;
    snprintf(s_banner_text, sizeof(s_banner_text), "%.90s", msg);
    s_banner_frames = 150; /* ~2.5s at 60fps */
}

static void start_fade_to(LobbyUiMode target) {
    if (s_mode == target && s_fade_phase == 0) return;
    s_fade_target = target;
    s_fade_phase = 1; /* FADE_OUT */
    if (s_fade_step == 0) s_fade_step = 1;
}

static const char* PROFILE_FILE = "bag2jp_online_profile.ini";

static void profile_load(void) {
    FILE* f = fopen(PROFILE_FILE, "r");
    if (!f) return;
    char line[128];
    while (fgets(line, sizeof(line), f)) {
        size_t n = strlen(line);
        while (n > 0 && (line[n - 1] == '\r' || line[n - 1] == '\n')) line[--n] = '\0';
        if (strncmp(line, "name=", 5) == 0 && line[5] != '\0') {
            snprintf(s_player_name, sizeof(s_player_name), "%.23s", line + 5);
        } else if (strncmp(line, "avatar=", 7) == 0) {
            int av = atoi(line + 7);
            if (av >= 0 && av < BAG2_AVATAR_COUNT) s_player_avatar = av;
        }
    }
    fclose(f);
}

static void profile_save(void) {
    FILE* f = fopen(PROFILE_FILE, "w");
    if (!f) return;
    fprintf(f, "name=%s\navatar=%d\n", s_player_name, s_player_avatar);
    fclose(f);
}

static int key_pressed(int vk) {
    if (vk > 0 && vk < 256 && s_frame_vk[vk]) {
        s_frame_vk[vk] = 0;
        return 1;
    }
    return 0;
}

static void poll_text_input(char* buf, int* len, int max_len) {
#ifdef _WIN32
    if (key_pressed(VK_BACK) && *len > 0) {
        buf[--(*len)] = '\0';
        return;
    }
    for (int vk = 'A'; vk <= 'Z'; ++vk) {
        if (key_pressed(vk) && *len < max_len - 1) {
            int shift = (GetAsyncKeyState(VK_SHIFT) & 0x8000) != 0;
            buf[(*len)++] = (char)(shift ? vk : (vk + 32));
            buf[*len] = '\0';
        }
    }
    for (int vk = '0'; vk <= '9'; ++vk) {
        if (key_pressed(vk) && *len < max_len - 1) {
            buf[(*len)++] = (char)vk;
            buf[*len] = '\0';
        }
    }
    if (key_pressed(VK_SPACE) && *len < max_len - 1) {
        buf[(*len)++] = ' ';
        buf[*len] = '\0';
    }
#else
    (void)buf; (void)len; (void)max_len;
#endif
}

static void cycle_avatar(void) {
    s_player_avatar = (s_player_avatar + 1) % BAG2_AVATAR_COUNT;
    profile_save();
    play_ui_sfx("sfx_cursor.wav");
    if (s_mode == UI_ROOM) {
        bag2jp_lobby_set_avatar(s_player_avatar);
    }
}

void bag2jp_lobby_ui_open(int open) {
    if (open) {
        if (s_mode == UI_CLOSED) {
            s_mode = UI_LOBBY;
            s_fade_phase = 2; /* FADE_IN from black */
            s_fade_step = 14;
            s_selected_room = 0;
            s_local_ready = 0;
            s_editing_name = 0;
            s_chat_len = 0;
            s_chat_input[0] = '\0';
            s_banner_frames = 0;
            psx_host_set_ui_capture(1);
            if (!bag2jp_lobby_state()->connected) {
                bag2jp_lobby_connect(s_server_host, s_server_port);
            }
            bag2jp_lobby_list_rooms();
            host_osd_set_status("");
        }
    } else {
        if (s_mode == UI_ROOM) {
            bag2jp_lobby_leave_room();
        }
        play_ui_sfx("sfx_cancel.wav");
        start_fade_to(UI_CLOSED);
        host_osd_set_status("");
    }
}

int bag2jp_lobby_ui_is_open(void) {
    return (s_mode != UI_CLOSED) || (s_fade_phase != 0);
}

void bag2jp_lobby_ui_tick(void) {
#ifdef _WIN32
    memcpy(s_frame_vk, s_sink_vk, sizeof(s_frame_vk));
    memset(s_sink_vk, 0, sizeof(s_sink_vk));
    s_frame_counter++;
    if (s_banner_frames > 0) s_banner_frames--;

    /* Advance P1 fade-to-black state machine */
    if (s_fade_phase == 1) {
        s_fade_step++;
        if (s_fade_step >= 14) {
            s_mode = s_fade_target;
            s_fade_phase = (s_mode == UI_CLOSED) ? 0 : 2;
            if (s_mode == UI_CLOSED) {
                s_fade_step = 0;
                psx_host_set_ui_capture(0);
                if (!s_in_online_match) bag2jp_netsync_disconnect_lobby();
            }
        }
        return;
    } else if (s_fade_phase == 2) {
        if (s_fade_step > 0) s_fade_step--;
        if (s_fade_step <= 0) s_fade_phase = 0;
    }

    if (key_pressed(VK_F9)) {
        bag2jp_lobby_ui_open(s_mode == UI_CLOSED ? 1 : 0);
    }
    if (s_mode == UI_CLOSED) return;

    bag2jp_lobby_poll();
    const LobbyClientState* st = bag2jp_lobby_state();

    /* P2/P3: React to incoming chat, READY!, and server errors */
    if (st->chat_count > s_prev_chat_count) {
        play_ui_sfx("sfx_chat.wav");
    }
    s_prev_chat_count = st->chat_count;

    if (st->guest_ready && !s_prev_guest_ready) {
        play_ui_sfx("sfx_ready.wav");
    }
    s_prev_guest_ready = st->guest_ready;

    if (st->last_error[0] && strcmp(st->last_error, s_prev_error) != 0) {
        snprintf(s_prev_error, sizeof(s_prev_error), "%.120s", st->last_error);
        play_ui_sfx("sfx_error.wav");
        show_banner(st->last_error);
    }

    if (st->match_started && st->match_room_code[0]) {
        play_ui_sfx("sfx_confirm.wav");
        bag2jp_netsync_apply_lobby_match(st->match_room_code);
        s_in_online_match = 1;
        s_pending_start_2p = 1;
        psx_host_set_ui_capture(0);
        start_fade_to(UI_CLOSED);
        host_osd_set_status("");
        return;
    }

    if (st->in_room && s_mode == UI_LOBBY) {
        s_local_ready = 0;
        s_editing_name = 0;
        s_prev_chat_count = 0;
        s_prev_guest_ready = 0;
        play_ui_sfx("sfx_confirm.wav");
        start_fade_to(UI_ROOM);
        return;
    } else if (!st->in_room && s_mode == UI_ROOM) {
        bag2jp_lobby_list_rooms();
        start_fade_to(UI_LOBBY);
        return;
    }

    /* P3: Auto-refresh room list every 3s in Lobby */
    if (s_mode == UI_LOBBY && st->connected && (s_frame_counter % 180) == 0) {
        bag2jp_lobby_list_rooms();
    }

    /* P4: Poll XInput gamepad edges (DPad=0x0001..8, Start=0x0010, LB=0x0100, RB=0x0200, A=0x1000, B=0x2000) */
    uint16_t pad = poll_gamepad_edges();

    if (key_pressed(VK_ESCAPE) || (pad & 0x2000)) {
        if (s_editing_name) {
            s_editing_name = 0;
            play_ui_sfx("sfx_cancel.wav");
        } else if (s_mode == UI_ROOM) {
            bag2jp_lobby_leave_room();
            play_ui_sfx("sfx_cancel.wav");
            bag2jp_lobby_list_rooms();
            start_fade_to(UI_LOBBY);
        } else {
            bag2jp_lobby_ui_open(0);
        }
        return;
    }

    if (s_mode == UI_LOBBY) {
        if (s_editing_name) {
            int nlen = (int)strlen(s_player_name);
            poll_text_input(s_player_name, &nlen, 20);
            if (key_pressed(VK_RETURN)) {
                if (s_player_name[0] == '\0') snprintf(s_player_name, sizeof(s_player_name), "Player");
                profile_save();
                play_ui_sfx("sfx_confirm.wav");
                s_editing_name = 0;
            }
            return;
        }
        if (key_pressed('P') || (pad & 0x0300)) cycle_avatar();
        if (key_pressed('N')) { s_editing_name = 1; play_ui_sfx("sfx_cursor.wav"); }
        if (key_pressed('R')) { bag2jp_lobby_list_rooms(); play_ui_sfx("sfx_cursor.wav"); }
        if (key_pressed('C')) {
            char rname[48];
            snprintf(rname, sizeof(rname), "%.16s'S ROOM", s_player_name);
            bag2jp_lobby_create_room(rname, s_player_name, s_player_avatar, 0);
        }
        if (key_pressed(VK_UP) || key_pressed(VK_LEFT) || (pad & 0x0005)) {
            if (s_selected_room > 0) { s_selected_room--; play_ui_sfx("sfx_cursor.wav"); }
        }
        if (key_pressed(VK_DOWN) || key_pressed(VK_RIGHT) || (pad & 0x000A)) {
            if (s_selected_room + 1 < st->room_count) { s_selected_room++; play_ui_sfx("sfx_cursor.wav"); }
        }
        if ((key_pressed(VK_RETURN) || (pad & 0x1000)) && st->room_count > 0 && s_selected_room < st->room_count) {
            bag2jp_lobby_join_room(st->rooms[s_selected_room].room_id, s_player_name, s_player_avatar, 0);
        }
    } else if (s_mode == UI_ROOM) {
        if (key_pressed(VK_F4) || (pad & 0x0300)) {
            cycle_avatar();
        } else if (st->is_host && key_pressed(VK_F7) && st->guest_name[0]) {
            bag2jp_lobby_kick_guest();
            play_ui_sfx("sfx_cancel.wav");
            show_banner("GUEST KICKED");
        } else if (st->is_host && (key_pressed(VK_F6) || (pad & 0x0010))) {
            if (!st->guest_name[0] || !st->guest_ready) {
                play_ui_sfx("sfx_error.wav");
                show_banner("GUEST IS NOT READY!");
            }
            bag2jp_lobby_start_match();
        } else if (!st->is_host && (key_pressed(VK_F5) || (pad & 0x0010))) {
            s_local_ready = !s_local_ready;
            bag2jp_lobby_set_ready(s_local_ready);
        } else {
            poll_text_input(s_chat_input, &s_chat_len, (int)sizeof(s_chat_input) - 1);
            if (key_pressed(VK_RETURN) && s_chat_len > 0) {
                bag2jp_lobby_send_chat(s_chat_input);
                s_chat_len = 0;
                s_chat_input[0] = '\0';
            }
        }
    }
#endif
}

#ifdef _WIN32
/* Compact 5x7 uppercase/ASCII pixel-art font for PS1 UI rendering via glScissor+glClear */
static const uint8_t* glyph_5x7(char c) {
    static const uint8_t g_sp[7] = {0,0,0,0,0,0,0};
    static const uint8_t g_ex[7] = {4,4,4,4,4,0,4};
    static const uint8_t g_ha[7] = {10,31,10,10,31,10,0};
    static const uint8_t g_ap[7] = {4,4,0,0,0,0,0};
    static const uint8_t g_lp[7] = {2,4,8,8,8,4,2};
    static const uint8_t g_rp[7] = {8,4,2,2,2,4,8};
    static const uint8_t g_mi[7] = {0,0,0,31,0,0,0};
    static const uint8_t g_dt[7] = {0,0,0,0,0,4,4};
    static const uint8_t g_sl[7] = {1,2,2,4,8,8,16};
    static const uint8_t g_cl[7] = {0,4,4,0,4,4,0};
    static const uint8_t g_gt[7] = {16,8,4,2,4,8,16};
    static const uint8_t g_qm[7] = {14,17,2,4,4,0,4};
    static const uint8_t g_lb[7] = {14,8,8,8,8,8,14};
    static const uint8_t g_rb[7] = {14,2,2,2,2,2,14};
    static const uint8_t g_us[7] = {0,0,0,0,0,0,31};
    static const uint8_t g_num[10][7] = {
        {14,17,19,21,25,17,14}, {4,12,4,4,4,4,14},     {14,17,1,6,8,16,31},
        {30,1,1,14,1,1,30},     {2,6,10,18,31,2,2},    {31,16,30,1,1,17,14},
        {14,16,30,17,17,17,14}, {31,1,2,4,8,8,8},      {14,17,17,14,17,17,14},
        {14,17,17,15,1,2,12}
    };
    static const uint8_t g_alp[26][7] = {
        {14,17,17,31,17,17,17}, {30,17,17,30,17,17,30}, {14,17,16,16,16,17,14},
        {28,18,17,17,17,18,28}, {31,16,16,30,16,16,31}, {31,16,16,30,16,16,16},
        {14,17,16,23,17,17,14}, {17,17,17,31,17,17,17}, {14,4,4,4,4,4,14},
        {7,2,2,2,18,18,12},     {17,18,20,24,20,18,17}, {16,16,16,16,16,16,31},
        {17,27,21,21,17,17,17}, {17,25,21,19,17,17,17}, {14,17,17,17,17,17,14},
        {30,17,17,30,16,16,16}, {14,17,17,17,21,18,13}, {30,17,17,30,20,18,17},
        {15,16,16,14,1,1,30},   {31,4,4,4,4,4,4},       {17,17,17,17,17,17,14},
        {17,17,17,17,17,10,4},  {17,17,17,21,21,27,17}, {17,17,10,4,10,17,17},
        {17,17,10,4,4,4,4},     {31,1,2,4,8,16,31}
    };
    unsigned char uc = (unsigned char)toupper((unsigned char)c);
    if (uc >= '0' && uc <= '9') return g_num[uc - '0'];
    if (uc >= 'A' && uc <= 'Z') return g_alp[uc - 'A'];
    switch (uc) {
        case '!': return g_ex; case '#': return g_ha; case '\'': return g_ap;
        case '(': return g_lp; case ')': return g_rp; case '-': return g_mi;
        case '.': return g_dt; case '/': return g_sl; case ':': return g_cl;
        case '>': return g_gt; case '?': return g_qm; case '[': return g_lb;
        case ']': return g_rb; case '_': return g_us; default: return g_sp;
    }
}

typedef struct {
    int ox, oy, cw, ch; /* 4:3 PS1 canvas in window pixels */
} Ps1Canvas;

static void fill_px(int x, int y_top, int w, int h, int win_h, float r, float g, float b) {
    if (w <= 0 || h <= 0) return;
    int y_gl = win_h - y_top - h;
    glScissor(x, y_gl, w, h);
    glClearColor(r, g, b, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);
}

static void fill_c(const Ps1Canvas* c, int win_h, float nx, float ny, float nw, float nh,
                   float r, float g, float b) {
    int x = c->ox + (int)(nx * c->cw);
    int y = c->oy + (int)(ny * c->ch);
    int w = (int)(nw * c->cw);
    int h = (int)(nh * c->ch);
    fill_px(x, y, w, h, win_h, r, g, b);
}

static void draw_box_c(const Ps1Canvas* c, int win_h, float nx, float ny, float nw, float nh,
                       int border_px, float r, float g, float b, float br, float bg, float bb) {
    int x = c->ox + (int)(nx * c->cw);
    int y = c->oy + (int)(ny * c->ch);
    int w = (int)(nw * c->cw);
    int h = (int)(nh * c->ch);
    fill_px(x, y, w, h, win_h, br, bg, bb);
    fill_px(x + border_px, y + border_px, w - 2 * border_px, h - 2 * border_px, win_h, r, g, b);
}

static void draw_text_px(int x, int y_top, int scale, int win_h, const char* text,
                         float r, float g, float b, int outline, float or_, float og, float ob) {
    if (!text) return;
    int cx = x;
    for (const char* p = text; *p; ++p) {
        const uint8_t* rows = glyph_5x7(*p);
        if (outline) {
            for (int ry = 0; ry < 7; ++ry) {
                for (int rx = 0; rx < 5; ++rx) {
                    if (rows[ry] & (1 << (4 - rx))) {
                        fill_px(cx + rx * scale - 1, y_top + ry * scale - 1, scale + 2, scale + 2, win_h, or_, og, ob);
                    }
                }
            }
        }
        for (int ry = 0; ry < 7; ++ry) {
            for (int rx = 0; rx < 5; ++rx) {
                if (rows[ry] & (1 << (4 - rx))) {
                    fill_px(cx + rx * scale, y_top + ry * scale, scale, scale, win_h, r, g, b);
                }
            }
        }
        cx += 6 * scale;
    }
}

static void draw_text_c(const Ps1Canvas* c, int win_h, float nx, float ny, int scale,
                        const char* text, float r, float g, float b, int outline, float or_, float og, float ob) {
    int x = c->ox + (int)(nx * c->cw);
    int y = c->oy + (int)(ny * c->ch);
    draw_text_px(x, y, scale, win_h, text, r, g, b, outline, or_, og, ob);
}

#define AVATAR_TEX_W 128
#define AVATAR_TEX_H 160

typedef void (APIENTRY *PFN_glGenFramebuffers)(GLsizei, GLuint*);
typedef void (APIENTRY *PFN_glBindFramebuffer)(GLenum, GLuint);
typedef void (APIENTRY *PFN_glFramebufferTexture2D)(GLenum, GLenum, GLenum, GLuint, GLint);
typedef void (APIENTRY *PFN_glBlitFramebuffer)(GLint, GLint, GLint, GLint, GLint, GLint, GLint, GLint, GLbitfield, GLenum);

#ifndef GL_READ_FRAMEBUFFER
#define GL_READ_FRAMEBUFFER 0x8CA8
#endif
#ifndef GL_DRAW_FRAMEBUFFER
#define GL_DRAW_FRAMEBUFFER 0x8CA9
#endif
#ifndef GL_DRAW_FRAMEBUFFER_BINDING
#define GL_DRAW_FRAMEBUFFER_BINDING 0x8CA6
#endif
#ifndef GL_READ_FRAMEBUFFER_BINDING
#define GL_READ_FRAMEBUFFER_BINDING 0x8CAA
#endif
#ifndef GL_COLOR_ATTACHMENT0
#define GL_COLOR_ATTACHMENT0 0x8CE0
#endif

static int s_gl_fbo_init = 0;
static PFN_glGenFramebuffers p_glGenFramebuffers = NULL;
static PFN_glBindFramebuffer p_glBindFramebuffer = NULL;
static PFN_glFramebufferTexture2D p_glFramebufferTexture2D = NULL;
static PFN_glBlitFramebuffer p_glBlitFramebuffer = NULL;
static GLuint s_avatar_fbo = 0;
static GLuint s_avatar_tex[BAG2_AVATAR_COUNT] = {0};
static int s_avatar_tried[BAG2_AVATAR_COUNT] = {0};

typedef struct {
    const char* path;
    int w, h;
    GLuint tex;
    int tried;
} UiSpriteTex;

static UiSpriteTex s_ui_sprites[5] = {
    { "online_avatars/hdr_lobby.rgba",  320,  56, 0, 0 },
    { "online_avatars/hdr_room.rgba",   320,  56, 0, 0 },
    { "online_avatars/vs_badge.rgba",    96,  64, 0, 0 },
    { "online_avatars/side_left.rgba",   48, 448, 0, 0 },
    { "online_avatars/side_right.rgba",  48, 448, 0, 0 }
};

static int init_fbo_procs(void) {
    if (!s_gl_fbo_init) {
        s_gl_fbo_init = 1;
        p_glGenFramebuffers = (PFN_glGenFramebuffers)wglGetProcAddress("glGenFramebuffers");
        p_glBindFramebuffer = (PFN_glBindFramebuffer)wglGetProcAddress("glBindFramebuffer");
        p_glFramebufferTexture2D = (PFN_glFramebufferTexture2D)wglGetProcAddress("glFramebufferTexture2D");
        p_glBlitFramebuffer = (PFN_glBlitFramebuffer)wglGetProcAddress("glBlitFramebuffer");
        if (p_glGenFramebuffers && p_glBindFramebuffer && p_glFramebufferTexture2D && p_glBlitFramebuffer) {
            p_glGenFramebuffers(1, &s_avatar_fbo);
        }
    }
    return s_avatar_fbo != 0;
}

static GLuint load_rgba_tex(const char* path, int w, int h) {
    FILE* f = fopen(path, "rb");
    if (!f) return 0;
    size_t sz = (size_t)w * (size_t)h * 4;
    unsigned char* pixels = (unsigned char*)malloc(sz);
    if (!pixels) { fclose(f); return 0; }
    size_t rd = fread(pixels, 1, sz, f);
    fclose(f);
    if (rd != sz) { free(pixels); return 0; }

    GLuint tex = 0;
    glGenTextures(1, &tex);
    glBindTexture(GL_TEXTURE_2D, tex);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, pixels);
    glBindTexture(GL_TEXTURE_2D, 0);
    free(pixels);
    return tex;
}

static int blit_ui_sprite(int idx, const Ps1Canvas* c, int win_h, float nx, float ny, float nw, float nh) {
    if (idx < 0 || idx >= 5 || !init_fbo_procs()) return 0;
    UiSpriteTex* sp = &s_ui_sprites[idx];
    if (!sp->tex && !sp->tried) {
        sp->tried = 1;
        sp->tex = load_rgba_tex(sp->path, sp->w, sp->h);
    }
    if (!sp->tex) return 0;
    int x0 = c->ox + (int)(nx * c->cw);
    int y_top = c->oy + (int)(ny * c->ch);
    int pw = (int)(nw * c->cw);
    int ph = (int)(nh * c->ch);
    int y0 = win_h - y_top - ph;
    GLint prev_draw = 0, prev_read = 0;
    glGetIntegerv(GL_DRAW_FRAMEBUFFER_BINDING, &prev_draw);
    glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING, &prev_read);
    glDisable(GL_SCISSOR_TEST);
    p_glBindFramebuffer(GL_READ_FRAMEBUFFER, s_avatar_fbo);
    p_glFramebufferTexture2D(GL_READ_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, sp->tex, 0);
    p_glBindFramebuffer(GL_DRAW_FRAMEBUFFER, (GLuint)prev_draw);
    p_glBlitFramebuffer(0, 0, sp->w, sp->h, x0, y0, x0 + pw, y0 + ph, GL_COLOR_BUFFER_BIT, GL_LINEAR);
    p_glBindFramebuffer(GL_READ_FRAMEBUFFER, (GLuint)prev_read);
    p_glBindFramebuffer(GL_DRAW_FRAMEBUFFER, (GLuint)prev_draw);
    glEnable(GL_SCISSOR_TEST);
    return 1;
}

static int ensure_avatar_tex(int avatar_id) {
    if (avatar_id < 0 || avatar_id >= BAG2_AVATAR_COUNT || !init_fbo_procs()) return 0;
    if (s_avatar_tex[avatar_id]) return 1;
    if (s_avatar_tried[avatar_id]) return 0;
    s_avatar_tried[avatar_id] = 1;
    char path[128];
    snprintf(path, sizeof(path), "online_avatars/avatar_%d.rgba", avatar_id);
    s_avatar_tex[avatar_id] = load_rgba_tex(path, AVATAR_TEX_W, AVATAR_TEX_H);
    return s_avatar_tex[avatar_id] != 0;
}

static void draw_avatar_portrait(const Ps1Canvas* c, int win_h, float nx, float ny, float nw, float nh,
                                 int avatar_id, int empty, const char* label) {
    if (avatar_id < 0 || avatar_id >= BAG2_AVATAR_COUNT) avatar_id = 0;
    const Bag2AvatarInfo* av = &s_avatars[avatar_id];
    int s = c->ch / 220;
    if (s < 2) s = 2;
    /* Outer black PS1 frame + flat shadow */
    fill_c(c, win_h, nx + 0.012f, ny + 0.015f, nw, nh, 0.25f, 0.25f, 0.28f);
    if (empty) {
        draw_box_c(c, win_h, nx, ny, nw, nh, 3, 0.78f, 0.80f, 0.82f, 0.08f, 0.08f, 0.10f);
        draw_text_c(c, win_h, nx + nw * 0.42f, ny + nh * 0.36f, s * 2, "?", 0.45f, 0.48f, 0.52f, 0, 0, 0, 0);
        return;
    }
    draw_box_c(c, win_h, nx, ny, nw, nh, 3, av->r, av->g, av->b, 0.06f, 0.06f, 0.08f);
    if (ensure_avatar_tex(avatar_id)) {
        int x0 = c->ox + (int)(nx * c->cw) + 3;
        int y_top = c->oy + (int)(ny * c->ch) + 3;
        int pw = (int)(nw * c->cw) - 6;
        int ph = (int)(nh * c->ch) - 6;
        int y0 = win_h - y_top - ph;
        GLint prev_draw = 0, prev_read = 0;
        glGetIntegerv(GL_DRAW_FRAMEBUFFER_BINDING, &prev_draw);
        glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING, &prev_read);
        glDisable(GL_SCISSOR_TEST);
        p_glBindFramebuffer(GL_READ_FRAMEBUFFER, s_avatar_fbo);
        p_glFramebufferTexture2D(GL_READ_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, s_avatar_tex[avatar_id], 0);
        p_glBindFramebuffer(GL_DRAW_FRAMEBUFFER, (GLuint)prev_draw);
        p_glBlitFramebuffer(0, 0, AVATAR_TEX_W, AVATAR_TEX_H, x0, y0, x0 + pw, y0 + ph, GL_COLOR_BUFFER_BIT, GL_LINEAR);
        p_glBindFramebuffer(GL_READ_FRAMEBUFFER, (GLuint)prev_read);
        p_glBindFramebuffer(GL_DRAW_FRAMEBUFFER, (GLuint)prev_draw);
        glEnable(GL_SCISSOR_TEST);
    } else {
        /* Fallback stylized silhouette */
        fill_c(c, win_h, nx + 0.012f, ny + nh * 0.68f, nw - 0.024f, nh * 0.28f, av->acc_r, av->acc_g, av->acc_b);
        fill_c(c, win_h, nx + nw * 0.32f, ny + nh * 0.14f, nw * 0.36f, nh * 0.32f, 0.10f, 0.10f, 0.12f);
        fill_c(c, win_h, nx + nw * 0.22f, ny + nh * 0.48f, nw * 0.56f, nh * 0.26f, 0.10f, 0.10f, 0.12f);
    }
    /* User name plate at bottom of portrait */
    fill_c(c, win_h, nx + 0.008f, ny + nh - 0.055f, nw - 0.016f, 0.048f, 0.08f, 0.08f, 0.12f);
    draw_text_c(c, win_h, nx + 0.022f, ny + nh - 0.045f, s, (label && label[0]) ? label : "PLAYER", 0.98f, 0.95f, 0.25f, 0, 0, 0, 0);
}

static void lobby_draw_cb(int fb_w, int fb_h, void* ctx) {
    (void)ctx;
    if (s_mode == UI_CLOSED || fb_w <= 0 || fb_h <= 0) return;

    const LobbyClientState* st = bag2jp_lobby_state();
    GLboolean scissor_was = glIsEnabled(GL_SCISSOR_TEST);
    GLint prev_scissor[4];
    GLfloat prev_clear[4];
    glGetIntegerv(GL_SCISSOR_BOX, prev_scissor);
    glGetFloatv(GL_COLOR_CLEAR_VALUE, prev_clear);
    glEnable(GL_SCISSOR_TEST);

    /* Center 4:3 PS1 canvas inside window */
    Ps1Canvas c;
    c.ch = fb_h;
    c.cw = (fb_h * 4) / 3;
    if (c.cw > fb_w) {
        c.cw = fb_w;
        c.ch = (fb_w * 3) / 4;
    }
    c.ox = (fb_w - c.cw) / 2;
    c.oy = (fb_h - c.ch) / 2;

    int s_sm = c.ch / 260; if (s_sm < 2) s_sm = 2;
    int s_md = c.ch / 190; if (s_md < 2) s_md = 2;
    int s_lg = c.ch / 115; if (s_lg < 3) s_lg = 3;

    if (s_mode == UI_LOBBY) {
        /* Flat sky-blue PS1 background + vertical graffiti side-banners */
        fill_c(&c, fb_h, 0.0f, 0.0f, 1.0f, 1.0f, 0.40f, 0.72f, 0.91f);
        if (!blit_ui_sprite(3, &c, fb_h, 0.0f, 0.0f, 0.072f, 0.930f)) {
            fill_c(&c, fb_h, 0.0f, 0.0f, 0.065f, 1.0f, 0.85f, 0.72f, 0.12f);
            fill_c(&c, fb_h, 0.012f, 0.04f, 0.040f, 0.92f, 0.18f, 0.78f, 0.24f);
        }
        if (!blit_ui_sprite(4, &c, fb_h, 0.928f, 0.0f, 0.072f, 0.930f)) {
            fill_c(&c, fb_h, 0.935f, 0.0f, 0.065f, 1.0f, 0.85f, 0.72f, 0.12f);
            fill_c(&c, fb_h, 0.948f, 0.04f, 0.040f, 0.92f, 0.18f, 0.78f, 0.24f);
        }

        /* Custom BAG2 graffiti header (with fallback) */
        if (!blit_ui_sprite(0, &c, fb_h, 0.20f, 0.020f, 0.60f, 0.105f)) {
            draw_text_c(&c, fb_h, 0.24f, 0.045f, s_lg, "ONLINE LOBBY", 0.99f, 0.88f, 0.10f, 1, 0.82f, 0.08f, 0.06f);
        }

        /* Top-right Profile badge (nickname + avatar) */
        char prof[64];
        snprintf(prof, sizeof(prof), "%s%s [%s]", s_player_name, s_editing_name ? "_" : "", s_avatars[s_player_avatar].name);
        draw_box_c(&c, fb_h, 0.09f, 0.135f, 0.82f, 0.060f, 2, 0.68f, 0.85f, 0.96f, 0.08f, 0.08f, 0.10f);
        draw_text_c(&c, fb_h, 0.11f, 0.150f, s_sm, prof, 0.08f, 0.10f, 0.16f, 0, 0, 0, 0);

        /* 2x4 Grid of PS1 rounded-look white tiles with flat grey offset shadow */
        for (int i = 0; i < 8; ++i) {
            int col = i % 4;
            int row = i / 4;
            float rx = 0.095f + col * 0.208f;
            float ry = 0.225f + row * 0.265f;
            float rw = 0.186f;
            float rh = 0.235f;

            /* Flat grey PS1 drop shadow */
            fill_c(&c, fb_h, rx + 0.010f, ry + 0.014f, rw, rh, 0.35f, 0.42f, 0.48f);

            if (i < st->room_count) {
                const LobbyRoomSummary* rm = &st->rooms[i];
                int sel = (i == s_selected_room);
                int playing = (strcmp(rm->state, "Playing") == 0);
                if (sel) {
                    draw_box_c(&c, fb_h, rx, ry, rw, rh, 4, 0.98f, 0.98f, 0.99f, 0.86f, 0.06f, 0.28f);
                    /* 1P red tab */
                    fill_c(&c, fb_h, rx, ry, 0.055f, 0.042f, 0.86f, 0.06f, 0.28f);
                    draw_text_c(&c, fb_h, rx + 0.008f, ry + 0.009f, s_sm, "1P", 1.0f, 1.0f, 1.0f, 0, 0, 0, 0);
                } else {
                    draw_box_c(&c, fb_h, rx, ry, rw, rh, 2, 0.98f, 0.98f, 0.99f, 0.72f, 0.76f, 0.80f);
                }
                char id_s[16], nm_s[16], st_s[16];
                snprintf(id_s, sizeof(id_s), "#%d", rm->room_id);
                snprintf(nm_s, sizeof(nm_s), "%.10s", rm->room_name);
                snprintf(st_s, sizeof(st_s), "%s %d/%d", playing ? "PLAY" : "WAIT", rm->players, rm->max_players);
                draw_text_c(&c, fb_h, rx + 0.065f, ry + 0.025f, s_sm, id_s, 0.08f, 0.08f, 0.10f, 0, 0, 0, 0);
                draw_text_c(&c, fb_h, rx + 0.014f, ry + 0.085f, s_sm, nm_s, 0.08f, 0.08f, 0.10f, 0, 0, 0, 0);
                fill_c(&c, fb_h, rx + 0.014f, ry + 0.165f, rw - 0.028f, 0.050f,
                       playing ? 0.92f : 0.10f, playing ? 0.48f : 0.64f, playing ? 0.06f : 0.16f);
                draw_text_c(&c, fb_h, rx + 0.022f, ry + 0.178f, s_sm, st_s, 1.0f, 1.0f, 1.0f, 0, 0, 0, 0);
            } else {
                /* Empty muted '?' tile */
                fill_c(&c, fb_h, rx, ry, rw, rh, 0.80f, 0.82f, 0.84f);
                draw_text_c(&c, fb_h, rx + 0.075f, ry + 0.082f, s_lg, "?", 0.50f, 0.54f, 0.58f, 0, 0, 0, 0);
            }
        }

        /* Translucent pale-blue info/status box */
        fill_c(&c, fb_h, 0.095f, 0.775f, 0.810f, 0.130f, 0.66f, 0.84f, 0.96f);
        char info1[80];
        if (!st->connected) {
            snprintf(info1, sizeof(info1), "DISCONNECTED: %.48s", st->last_error);
        } else if (st->room_count == 0) {
            snprintf(info1, sizeof(info1), "NO ROOMS YET. PRESS [C] TO CREATE A 1V1 ROOM");
        } else {
            snprintf(info1, sizeof(info1), "ROOMS: %d   PRESS [ENTER] TO JOIN SELECTED ROOM", st->room_count);
        }
        draw_text_c(&c, fb_h, 0.115f, 0.800f, s_sm, info1, 0.06f, 0.08f, 0.12f, 0, 0, 0, 0);
        draw_text_c(&c, fb_h, 0.115f, 0.855f, s_sm, "[P] CHANGE AVATAR   [N] EDIT NAME", 0.12f, 0.22f, 0.36f, 0, 0, 0, 0);

        /* Bottom white PS1 hotkey strip */
        fill_c(&c, fb_h, 0.0f, 0.930f, 1.0f, 0.070f, 0.94f, 0.96f, 0.98f);
        draw_text_c(&c, fb_h, 0.06f, 0.950f, s_sm, "[C] CREATE  [R] REFRESH  [ENTER] JOIN  [ESC] BACK", 0.06f, 0.06f, 0.08f, 0, 0, 0, 0);
    } else if (s_mode == UI_ROOM) {
        /* Exact Character Select split: Mustard-yellow (1P/HOST) | Sky-blue (2P/GUEST) */
        fill_c(&c, fb_h, 0.0f, 0.0f, 0.50f, 1.0f, 0.85f, 0.72f, 0.12f);
        fill_c(&c, fb_h, 0.50f, 0.0f, 0.50f, 1.0f, 0.40f, 0.72f, 0.91f);

        /* Custom BAG2 Room Header (with fallback) */
        if (!blit_ui_sprite(1, &c, fb_h, 0.20f, 0.020f, 0.60f, 0.105f)) {
            char hdr[48];
            snprintf(hdr, sizeof(hdr), "ROOM #%d - 1V1", st->room_id);
            draw_text_c(&c, fb_h, 0.24f, 0.040f, s_lg, hdr, 0.99f, 0.88f, 0.10f, 1, 0.82f, 0.08f, 0.06f);
        }

        /* Left (1P / HOST) name box + 1P flash tag */
        fill_c(&c, fb_h, 0.12f, 0.175f, 0.32f, 0.135f, 0.95f, 0.90f, 0.68f);
        draw_box_c(&c, fb_h, 0.03f, 0.180f, 0.10f, 0.085f, 2, 0.96f, 0.86f, 0.10f, 0.85f, 0.10f, 0.10f);
        draw_text_c(&c, fb_h, 0.055f, 0.205f, s_md, "1P", 0.88f, 0.08f, 0.08f, 0, 0, 0, 0);
        draw_text_c(&c, fb_h, 0.16f, 0.190f, s_sm, "HOST", 0.98f, 0.98f, 0.98f, 1, 0.86f, 0.42f, 0.08f);
        draw_text_c(&c, fb_h, 0.16f, 0.250f, s_sm, st->host_name[0] ? st->host_name : s_player_name, 0.08f, 0.08f, 0.10f, 0, 0, 0, 0);

        /* Right (2P / GUEST) name box + 2P flash tag + READY! badge */
        int has_guest = (st->guest_name[0] != '\0');
        fill_c(&c, fb_h, 0.56f, 0.175f, 0.32f, 0.135f, 0.78f, 0.90f, 0.98f);
        draw_box_c(&c, fb_h, 0.87f, 0.180f, 0.10f, 0.085f, 2, 0.16f, 0.72f, 0.98f, 0.08f, 0.16f, 0.55f);
        draw_text_c(&c, fb_h, 0.895f, 0.205f, s_md, "2P", 0.98f, 0.98f, 1.0f, 0, 0, 0, 0);
        draw_text_c(&c, fb_h, 0.58f, 0.215f, s_sm, has_guest ? st->guest_name : "WAITING...", 0.08f, 0.08f, 0.12f, 0, 0, 0, 0);
        if (has_guest && st->guest_ready) {
            draw_box_c(&c, fb_h, 0.76f, 0.295f, 0.18f, 0.075f, 2, 0.12f, 0.86f, 0.20f, 0.06f, 0.06f, 0.08f);
            draw_text_c(&c, fb_h, 0.785f, 0.315f, s_sm, "READY!", 0.04f, 0.12f, 0.04f, 0, 0, 0, 0);
        }

        /* Character Portraits (Host left, Guest right) with user name labels */
        const char* hname = st->host_name[0] ? st->host_name : s_player_name;
        const char* gname = has_guest ? st->guest_name : "WAITING...";
        draw_avatar_portrait(&c, fb_h, 0.11f, 0.355f, 0.24f, 0.365f, st->host_avatar, 0, hname);
        draw_avatar_portrait(&c, fb_h, 0.65f, 0.355f, 0.24f, 0.365f, st->guest_avatar, !has_guest, gname);

        /* Center VS emblem + START / READY button */
        if (!blit_ui_sprite(2, &c, fb_h, 0.41f, 0.400f, 0.18f, 0.125f)) {
            draw_text_c(&c, fb_h, 0.445f, 0.415f, s_lg, "VS", 0.98f, 0.98f, 0.98f, 1, 0.06f, 0.06f, 0.08f);
        }
        int can_start = (st->is_host && has_guest && st->guest_ready);
        fill_c(&c, fb_h, 0.388f, 0.635f, 0.24f, 0.085f, 0.25f, 0.28f, 0.32f); /* flat grey shadow */
        if (st->is_host) {
            draw_box_c(&c, fb_h, 0.38f, 0.625f, 0.24f, 0.085f, 2,
                       can_start ? 0.16f : 0.48f, can_start ? 0.82f : 0.52f, can_start ? 0.22f : 0.56f,
                       0.06f, 0.06f, 0.08f);
            draw_text_c(&c, fb_h, 0.405f, 0.652f, s_sm, can_start ? "START [F6]" : "WAIT READY", 1.0f, 1.0f, 1.0f, 0, 0, 0, 0);
        } else {
            draw_box_c(&c, fb_h, 0.38f, 0.625f, 0.24f, 0.085f, 2,
                       s_local_ready ? 0.16f : 0.22f, s_local_ready ? 0.82f : 0.52f, s_local_ready ? 0.22f : 0.92f,
                       0.06f, 0.06f, 0.08f);
            draw_text_c(&c, fb_h, 0.405f, 0.652f, s_sm, s_local_ready ? "READY [F5]" : "SET READY", 1.0f, 1.0f, 1.0f, 0, 0, 0, 0);
        }

        /* Bottom Dark-Navy Chat Box (P3: 2-line chat history + input) */
        draw_box_c(&c, fb_h, 0.08f, 0.745f, 0.84f, 0.168f, 2, 0.07f, 0.12f, 0.22f, 0.86f, 0.90f, 0.96f);
        if (st->chat_count >= 2) {
            const LobbyChatMsg* m0 = &st->chat[st->chat_count - 2];
            const LobbyChatMsg* m1 = &st->chat[st->chat_count - 1];
            char cl0[96], cl1[96];
            snprintf(cl0, sizeof(cl0), "[%.14s]: %.40s", m0->sender, m0->text);
            snprintf(cl1, sizeof(cl1), "[%.14s]: %.40s", m1->sender, m1->text);
            draw_text_c(&c, fb_h, 0.10f, 0.760f, s_sm, cl0, 0.65f, 0.78f, 0.90f, 0, 0, 0, 0);
            draw_text_c(&c, fb_h, 0.10f, 0.810f, s_sm, cl1, 0.55f, 0.92f, 0.98f, 0, 0, 0, 0);
        } else if (st->chat_count == 1) {
            const LobbyChatMsg* m = &st->chat[0];
            char cl[96];
            snprintf(cl, sizeof(cl), "[%.14s]: %.40s", m->sender, m->text);
            draw_text_c(&c, fb_h, 0.10f, 0.785f, s_sm, cl, 0.55f, 0.92f, 0.98f, 0, 0, 0, 0);
        }
        char inp[96];
        snprintf(inp, sizeof(inp), "> %.42s_", s_chat_input);
        draw_text_c(&c, fb_h, 0.10f, 0.862f, s_sm, inp, 0.96f, 0.96f, 0.98f, 0, 0, 0, 0);

        /* Bottom white PS1 hotkey strip */
        fill_c(&c, fb_h, 0.16f, 0.930f, 0.68f, 0.060f, 0.94f, 0.96f, 0.98f);
        draw_text_c(&c, fb_h, 0.20f, 0.946f, s_sm,
                    st->is_host ? "[F6] START [F7] KICK [F4] AVATAR [ESC] LEAVE" : "[F5] READY  [F4] AVATAR  [ESC] LEAVE",
                    0.06f, 0.06f, 0.08f, 0, 0, 0, 0);
    }

    /* P3: Temporary red PS1 error/alert banner */
    if (s_banner_frames > 0 && s_banner_text[0]) {
        draw_box_c(&c, fb_h, 0.16f, 0.525f, 0.68f, 0.080f, 3, 0.82f, 0.10f, 0.14f, 0.98f, 0.92f, 0.20f);
        draw_text_c(&c, fb_h, 0.21f, 0.550f, s_sm, s_banner_text, 1.0f, 1.0f, 1.0f, 0, 0, 0, 0);
    }

    /* P1: Smooth PS1 CRT scan-band fade-to-black transition (s_fade_step 0..14) */
    if (s_fade_step > 0) {
        int band = 14;
        int fill_h = (s_fade_step >= 14) ? band : ((s_fade_step * band + 7) / 14);
        if (fill_h >= band) {
            fill_c(&c, fb_h, 0.0f, 0.0f, 1.0f, 1.0f, 0.0f, 0.0f, 0.0f);
        } else if (fill_h > 0) {
            for (int y = c.oy; y < c.oy + c.ch; y += band) {
                int h = fill_h;
                if (y + h > c.oy + c.ch) h = (c.oy + c.ch) - y;
                fill_px(c.ox, y, c.cw, h, fb_h, 0.0f, 0.0f, 0.0f);
            }
        }
    }

    glClearColor(prev_clear[0], prev_clear[1], prev_clear[2], prev_clear[3]);
    glScissor(prev_scissor[0], prev_scissor[1], prev_scissor[2], prev_scissor[3]);
    if (!scissor_was) glDisable(GL_SCISSOR_TEST);
}
#endif

void bag2jp_lobby_ui_init(const char* server_host, uint16_t server_port,
                          const char* player_name, uint32_t content_id) {
    (void)content_id;
    if (server_host && server_host[0]) snprintf(s_server_host, sizeof(s_server_host), "%s", server_host);
    if (server_port > 0) s_server_port = server_port;
    if (player_name && player_name[0]) snprintf(s_player_name, sizeof(s_player_name), "%.23s", player_name);
    profile_load();
    const char* env_host = getenv("BAG2JP_LOBBY_HOST");
    if (env_host && env_host[0]) snprintf(s_server_host, sizeof(s_server_host), "%s", env_host);
    const char* env_port = getenv("BAG2JP_LOBBY_PORT");
    if (env_port && env_port[0]) {
        int p = atoi(env_port);
        if (p > 0 && p < 65536) s_server_port = (uint16_t)p;
    }
    const char* env_name = getenv("BAG2JP_PLAYER_NAME");
    if (env_name && env_name[0]) snprintf(s_player_name, sizeof(s_player_name), "%.23s", env_name);
#ifdef _WIN32
    psx_host_set_input_sink(lobby_input_sink, NULL);
    psx_host_overlay_set_draw_cb(lobby_draw_cb, NULL);
#endif
}

void bag2jp_lobby_ui_return_from_match(void) {
    if (!s_in_online_match) return;
    s_in_online_match = 0;
    s_local_ready = 0;
    bag2jp_lobby_finish_match();
    s_mode = UI_ROOM;
    s_fade_phase = 2; /* FADE_IN from black back into 1v1 Waiting Room */
    s_fade_step = 14;
    psx_host_set_ui_capture(1);
    host_osd_set_status("");
}

void bag2jp_lobby_ui_shutdown(void) {
    bag2jp_lobby_ui_open(0);
    bag2jp_lobby_disconnect();
}
