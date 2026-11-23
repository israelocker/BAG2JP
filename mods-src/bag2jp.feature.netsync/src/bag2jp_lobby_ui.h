#ifndef BAG2JP_LOBBY_UI_H
#define BAG2JP_LOBBY_UI_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

void bag2jp_lobby_ui_init(const char* server_host, uint16_t server_port,
                          const char* player_name, uint32_t content_id);
void bag2jp_lobby_ui_shutdown(void);
void bag2jp_lobby_ui_open(int open);
int  bag2jp_lobby_ui_is_open(void);
void bag2jp_lobby_ui_tick(void);
void bag2jp_lobby_ui_return_from_match(void);

#ifdef __cplusplus
}
#endif

#endif /* BAG2JP_LOBBY_UI_H */
