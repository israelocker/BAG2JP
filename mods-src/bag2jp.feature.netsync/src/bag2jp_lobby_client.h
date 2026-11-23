#ifndef BAG2JP_LOBBY_CLIENT_H
#define BAG2JP_LOBBY_CLIENT_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define LOBBY_MAX_ROOMS 32
#define LOBBY_MAX_CHAT  32

typedef struct {
    int room_id;
    char room_name[48];
    char host_name[32];
    int players;
    int max_players;
    char state[16]; /* "Waiting" | "Playing" */
} LobbyRoomSummary;

typedef struct {
    char sender[32];
    char text[208];
} LobbyChatMsg;

typedef struct {
    int connected;
    int in_room;
    int is_host;
    int room_id;
    char room_name[48];
    char host_name[32];
    int host_avatar;
    char guest_name[32];
    int guest_avatar;
    int guest_ready;
    char room_state[16];

    int match_started;
    char match_room_code[64];
    char last_error[128];

    int room_count;
    LobbyRoomSummary rooms[LOBBY_MAX_ROOMS];

    int chat_count;
    LobbyChatMsg chat[LOBBY_MAX_CHAT];
} LobbyClientState;

int bag2jp_lobby_connect(const char* host, uint16_t port);
void bag2jp_lobby_disconnect(void);
void bag2jp_lobby_poll(void);
const LobbyClientState* bag2jp_lobby_state(void);

int bag2jp_lobby_list_rooms(void);
int bag2jp_lobby_create_room(const char* room_name, const char* player_name, int avatar_id, uint32_t content_id);
int bag2jp_lobby_join_room(int room_id, const char* player_name, int avatar_id, uint32_t content_id);
int bag2jp_lobby_leave_room(void);
int bag2jp_lobby_set_ready(int ready);
int bag2jp_lobby_set_avatar(int avatar_id);
int bag2jp_lobby_send_chat(const char* text);
int bag2jp_lobby_start_match(void);
int bag2jp_lobby_finish_match(void);

#ifdef __cplusplus
}
#endif

#endif /* BAG2JP_LOBBY_CLIENT_H */
