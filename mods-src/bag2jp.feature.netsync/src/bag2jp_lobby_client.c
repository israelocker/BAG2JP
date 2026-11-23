#include "bag2jp_lobby_client.h"

#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static SOCKET s_sock = INVALID_SOCKET;
static LobbyClientState s_state;
static uint8_t s_rx_buf[16384];
static int s_rx_len = 0;

/* Mode: 1 = public MQTT brokers (default, zero-config), 0 = TCP lobby_server.py (when BAG2JP_LOBBY_HOST is set) */
static int s_use_mqtt = 1;
static uint16_t s_mqtt_mid = 1;
static uint64_t s_last_ping_ms = 0;
static uint64_t s_last_hb_ms = 0;
static int64_t s_room_ts[LOBBY_MAX_ROOMS];
static char s_local_name[32] = "Player";
static uint32_t s_room_content_id = 0;

#define LOBBY_ROOM_TTL_SEC 90
#define LOBBY_ROOM_HB_MS   25000

static void safe_copy(char* dst, size_t dst_sz, const char* src) {
    if (!dst || dst_sz == 0) return;
    if (!src) { dst[0] = '\0'; return; }
    snprintf(dst, dst_sz, "%s", src);
}

static int json_get_str(const char* json, const char* key, char* out, size_t out_sz) {
    char pat[64];
    snprintf(pat, sizeof(pat), "\"%s\":\"", key);
    const char* p = strstr(json, pat);
    if (!p) {
        snprintf(pat, sizeof(pat), "\"%s\": \"", key);
        p = strstr(json, pat);
        if (!p) return 0;
    }
    p += strlen(pat);
    size_t i = 0;
    while (*p && *p != '"' && i + 1 < out_sz) {
        if (*p == '\\' && p[1]) p++;
        out[i++] = *p++;
    }
    out[i] = '\0';
    return 1;
}

static int json_get_int(const char* json, const char* key, int* out) {
    char pat[64];
    snprintf(pat, sizeof(pat), "\"%s\":", key);
    const char* p = strstr(json, pat);
    if (!p) return 0;
    p += strlen(pat);
    while (*p == ' ') p++;
    if (strncmp(p, "true", 4) == 0) { *out = 1; return 1; }
    if (strncmp(p, "false", 5) == 0) { *out = 0; return 1; }
    *out = atoi(p);
    return 1;
}

static int json_get_u32(const char* json, const char* key, uint32_t* out) {
    char pat[64];
    snprintf(pat, sizeof(pat), "\"%s\":", key);
    const char* p = strstr(json, pat);
    if (!p) return 0;
    p += strlen(pat);
    while (*p == ' ') p++;
    *out = (uint32_t)strtoul(p, NULL, 10);
    return 1;
}

static int json_get_i64(const char* json, const char* key, int64_t* out) {
    char pat[64];
    snprintf(pat, sizeof(pat), "\"%s\":", key);
    const char* p = strstr(json, pat);
    if (!p) return 0;
    p += strlen(pat);
    while (*p == ' ') p++;
    *out = (int64_t)_strtoi64(p, NULL, 10);
    return 1;
}

static int send_all(const void* data, int len) {
    if (s_sock == INVALID_SOCKET || !s_state.connected) return -1;
    const char* p = (const char*)data;
    int left = len;
    while (left > 0) {
        int n = send(s_sock, p, left, 0);
        if (n <= 0) return -1;
        p += n;
        left -= n;
    }
    return 0;
}

static int send_line(const char* line) {
    return send_all(line, (int)strlen(line));
}

/* =========================== MQTT 3.1.1 Wire Helpers =========================== */

static int mqtt_put_rem_len(uint8_t* dst, int len) {
    int n = 0;
    do {
        uint8_t b = (uint8_t)(len % 128);
        len /= 128;
        if (len > 0) b |= 0x80u;
        dst[n++] = b;
    } while (len > 0 && n < 4);
    return n;
}

static int mqtt_send_connect(const char* cid) {
    uint8_t pkt[256];
    int cid_len = (int)strlen(cid);
    int rem = 10 + 2 + cid_len;
    int pos = 0;
    pkt[pos++] = 0x10; /* CONNECT */
    pos += mqtt_put_rem_len(pkt + pos, rem);
    pkt[pos++] = 0x00; pkt[pos++] = 0x04;
    pkt[pos++] = 'M'; pkt[pos++] = 'Q'; pkt[pos++] = 'T'; pkt[pos++] = 'T';
    pkt[pos++] = 0x04; /* Protocol Level 4 (3.1.1) */
    pkt[pos++] = 0x02; /* Clean Session */
    pkt[pos++] = 0x00; pkt[pos++] = 30; /* Keep Alive = 30s */
    pkt[pos++] = (uint8_t)((cid_len >> 8) & 0xFF);
    pkt[pos++] = (uint8_t)(cid_len & 0xFF);
    memcpy(pkt + pos, cid, (size_t)cid_len);
    pos += cid_len;
    return send_all(pkt, pos);
}

static int mqtt_send_sub(const char* topic) {
    uint8_t pkt[256];
    int tlen = (int)strlen(topic);
    if (tlen > 200) return -1;
    uint16_t mid = s_mqtt_mid++;
    if (s_mqtt_mid == 0) s_mqtt_mid = 1;
    int rem = 2 + 2 + tlen + 1;
    int pos = 0;
    pkt[pos++] = 0x82; /* SUBSCRIBE (QoS 1 required by spec) */
    pos += mqtt_put_rem_len(pkt + pos, rem);
    pkt[pos++] = (uint8_t)(mid >> 8);
    pkt[pos++] = (uint8_t)(mid & 0xFF);
    pkt[pos++] = (uint8_t)(tlen >> 8);
    pkt[pos++] = (uint8_t)(tlen & 0xFF);
    memcpy(pkt + pos, topic, (size_t)tlen);
    pos += tlen;
    pkt[pos++] = 0x00; /* QoS 0 */
    return send_all(pkt, pos);
}

static int mqtt_send_unsub(const char* topic) {
    uint8_t pkt[256];
    int tlen = (int)strlen(topic);
    if (tlen > 200) return -1;
    uint16_t mid = s_mqtt_mid++;
    if (s_mqtt_mid == 0) s_mqtt_mid = 1;
    int rem = 2 + 2 + tlen;
    int pos = 0;
    pkt[pos++] = 0xA2; /* UNSUBSCRIBE */
    pos += mqtt_put_rem_len(pkt + pos, rem);
    pkt[pos++] = (uint8_t)(mid >> 8);
    pkt[pos++] = (uint8_t)(mid & 0xFF);
    pkt[pos++] = (uint8_t)(tlen >> 8);
    pkt[pos++] = (uint8_t)(tlen & 0xFF);
    memcpy(pkt + pos, topic, (size_t)tlen);
    pos += tlen;
    return send_all(pkt, pos);
}

static int mqtt_send_pub(const char* topic, const char* payload, int retain) {
    uint8_t pkt[1024];
    int tlen = (int)strlen(topic);
    int plen = payload ? (int)strlen(payload) : 0;
    if (2 + tlen + plen + 8 > (int)sizeof(pkt)) return -1;
    int rem = 2 + tlen + plen;
    int pos = 0;
    pkt[pos++] = (uint8_t)(0x30 | (retain ? 0x01 : 0x00)); /* PUBLISH QoS 0 */
    pos += mqtt_put_rem_len(pkt + pos, rem);
    pkt[pos++] = (uint8_t)(tlen >> 8);
    pkt[pos++] = (uint8_t)(tlen & 0xFF);
    memcpy(pkt + pos, topic, (size_t)tlen);
    pos += tlen;
    if (plen > 0) {
        memcpy(pkt + pos, payload, (size_t)plen);
        pos += plen;
    }
    return send_all(pkt, pos);
}

static void mqtt_send_ping(void) {
    uint8_t pkt[2] = { 0xC0, 0x00 }; /* PINGREQ */
    (void)send_all(pkt, 2);
}

static void mqtt_publish_room_state(void) {
    if (!s_use_mqtt || !s_state.in_room || !s_state.is_host) return;
    char topic[96], body[512];
    snprintf(topic, sizeof(topic), "bag2jp/lobby/v1/rooms/%d", s_state.room_id);
    int players = s_state.guest_name[0] ? 2 : 1;
    long long now_ts = (long long)time(NULL);
    snprintf(body, sizeof(body),
             "{\"room_id\":%d,\"room_name\":\"%s\",\"host_name\":\"%s\",\"host_avatar\":%d,"
             "\"guest_name\":\"%s\",\"guest_avatar\":%d,\"guest_ready\":%d,\"players\":%d,"
             "\"max_players\":2,\"state\":\"%s\",\"content_id\":%u,\"ts\":%lld}",
             s_state.room_id, s_state.room_name, s_state.host_name, s_state.host_avatar,
             s_state.guest_name, s_state.guest_avatar, s_state.guest_ready ? 1 : 0, players,
             s_state.room_state[0] ? s_state.room_state : "Waiting", s_room_content_id, now_ts);
    s_last_hb_ms = GetTickCount64();
    (void)mqtt_send_pub(topic, body, 1);
}

static void mqtt_remove_room_summary(int room_id) {
    for (int i = 0; i < s_state.room_count; ++i) {
        if (s_state.rooms[i].room_id == room_id) {
            if (i + 1 < s_state.room_count) {
                memmove(&s_state.rooms[i], &s_state.rooms[i + 1],
                        sizeof(LobbyRoomSummary) * (size_t)(s_state.room_count - i - 1));
                memmove(&s_room_ts[i], &s_room_ts[i + 1],
                        sizeof(int64_t) * (size_t)(s_state.room_count - i - 1));
            }
            s_state.room_count--;
            return;
        }
    }
}

static void mqtt_prune_stale_rooms(void) {
    int64_t now_ts = (int64_t)time(NULL);
    for (int i = 0; i < s_state.room_count; ) {
        if (s_room_ts[i] > 0 && (now_ts - s_room_ts[i]) > LOBBY_ROOM_TTL_SEC) {
            int rid = s_state.rooms[i].room_id;
            mqtt_remove_room_summary(rid);
            if (s_state.in_room && !s_state.is_host && s_state.room_id == rid) {
                s_state.in_room = 0;
                safe_copy(s_state.last_error, sizeof(s_state.last_error), "Host timed out");
            }
        } else {
            ++i;
        }
    }
}

static void mqtt_upsert_room_summary(int room_id, const char* json) {
    int64_t ts = 0;
    int64_t now_ts = (int64_t)time(NULL);
    if (json_get_i64(json, "ts", &ts) && ts > 0 && (now_ts - ts) > LOBBY_ROOM_TTL_SEC) {
        mqtt_remove_room_summary(room_id);
        return; /* ignore stale ghost room */
    }
    int idx = -1;
    for (int i = 0; i < s_state.room_count; ++i) {
        if (s_state.rooms[i].room_id == room_id) {
            idx = i;
            break;
        }
    }
    if (idx < 0) {
        if (s_state.room_count >= LOBBY_MAX_ROOMS) return;
        idx = s_state.room_count++;
        memset(&s_state.rooms[idx], 0, sizeof(s_state.rooms[idx]));
        s_state.rooms[idx].room_id = room_id;
    }
    LobbyRoomSummary* dst = &s_state.rooms[idx];
    s_room_ts[idx] = ts > 0 ? ts : now_ts;
    json_get_str(json, "room_name", dst->room_name, sizeof(dst->room_name));
    json_get_str(json, "host_name", dst->host_name, sizeof(dst->host_name));
    if (!json_get_int(json, "players", &dst->players)) dst->players = 1;
    if (!json_get_int(json, "max_players", &dst->max_players)) dst->max_players = 2;
    if (!json_get_str(json, "state", dst->state, sizeof(dst->state))) {
        safe_copy(dst->state, sizeof(dst->state), "Waiting");
    }
}

static void append_chat(const char* sender, const char* text) {
    if (s_state.chat_count >= LOBBY_MAX_CHAT) {
        memmove(&s_state.chat[0], &s_state.chat[1],
                sizeof(LobbyChatMsg) * (LOBBY_MAX_CHAT - 1));
        s_state.chat_count = LOBBY_MAX_CHAT - 1;
    }
    LobbyChatMsg* m = &s_state.chat[s_state.chat_count++];
    safe_copy(m->sender, sizeof(m->sender), sender);
    safe_copy(m->text, sizeof(m->text), text);
}

static void mqtt_handle_publish(const char* topic, const char* payload, int plen) {
    const char* rooms_pfx = "bag2jp/lobby/v1/rooms/";
    if (strncmp(topic, rooms_pfx, strlen(rooms_pfx)) == 0) {
        int rid = atoi(topic + strlen(rooms_pfx));
        if (rid <= 0) return;
        if (plen <= 0 || payload[0] == '\0') {
            mqtt_remove_room_summary(rid);
            if (s_state.in_room && !s_state.is_host && s_state.room_id == rid) {
                s_state.in_room = 0;
                safe_copy(s_state.last_error, sizeof(s_state.last_error), "Host closed the room");
            }
            return;
        }
        mqtt_upsert_room_summary(rid, payload);
        if (s_state.in_room && s_state.room_id == rid) {
            json_get_str(payload, "room_name", s_state.room_name, sizeof(s_state.room_name));
            json_get_str(payload, "host_name", s_state.host_name, sizeof(s_state.host_name));
            json_get_int(payload, "host_avatar", &s_state.host_avatar);
            json_get_str(payload, "guest_name", s_state.guest_name, sizeof(s_state.guest_name));
            json_get_int(payload, "guest_avatar", &s_state.guest_avatar);
            json_get_int(payload, "guest_ready", &s_state.guest_ready);
            json_get_str(payload, "state", s_state.room_state, sizeof(s_state.room_state));
        }
        return;
    }

    char ev_topic[96];
    snprintf(ev_topic, sizeof(ev_topic), "bag2jp/lobby/v1/room/%d/ev", s_state.room_id);
    if (!s_state.in_room || strcmp(topic, ev_topic) != 0) return;

    char type[32] = {0};
    if (!json_get_str(payload, "type", type, sizeof(type))) return;

    if (strcmp(type, "chat") == 0) {
        char sender[32] = {0}, text[208] = {0};
        json_get_str(payload, "sender", sender, sizeof(sender));
        json_get_str(payload, "text", text, sizeof(text));
        append_chat(sender, text);
    } else if (strcmp(type, "match_start") == 0) {
        s_state.match_started = 1;
        json_get_str(payload, "room_code", s_state.match_room_code, sizeof(s_state.match_room_code));
    } else if (strcmp(type, "error") == 0) {
        json_get_str(payload, "msg", s_state.last_error, sizeof(s_state.last_error));
    } else if (s_state.is_host) {
        if (strcmp(type, "join") == 0) {
            char gname[32] = {0};
            int gava = 0;
            uint32_t gcid = 0;
            json_get_str(payload, "name", gname, sizeof(gname));
            json_get_int(payload, "avatar", &gava);
            json_get_u32(payload, "content_id", &gcid);
            if (s_state.guest_name[0] != '\0' && strcmp(s_state.guest_name, gname) != 0) {
                (void)mqtt_send_pub(ev_topic, "{\"type\":\"error\",\"msg\":\"Room is full\"}", 0);
            } else if (s_room_content_id != 0 && gcid != 0 && gcid != s_room_content_id) {
                (void)mqtt_send_pub(ev_topic, "{\"type\":\"error\",\"msg\":\"Content version mismatch\"}", 0);
            } else {
                safe_copy(s_state.guest_name, sizeof(s_state.guest_name), gname);
                s_state.guest_avatar = gava;
                s_state.guest_ready = 0;
                mqtt_publish_room_state();
            }
        } else if (strcmp(type, "leave") == 0) {
            s_state.guest_name[0] = '\0';
            s_state.guest_avatar = 0;
            s_state.guest_ready = 0;
            mqtt_publish_room_state();
        } else if (strcmp(type, "ready") == 0) {
            int rdy = 0;
            json_get_int(payload, "ready", &rdy);
            s_state.guest_ready = rdy ? 1 : 0;
            mqtt_publish_room_state();
        } else if (strcmp(type, "avatar") == 0) {
            char role[16] = {0};
            int ava = 0;
            json_get_str(payload, "role", role, sizeof(role));
            json_get_int(payload, "avatar", &ava);
            if (strcmp(role, "guest") == 0) s_state.guest_avatar = ava;
            else s_state.host_avatar = ava;
            mqtt_publish_room_state();
        }
    }
}

static void mqtt_process_rx(void) {
    while (s_rx_len >= 2) {
        uint8_t hdr = s_rx_buf[0];
        int mul = 1, rem = 0, pos = 1, ok = 0;
        while (pos < s_rx_len && pos <= 4) {
            uint8_t b = s_rx_buf[pos++];
            rem += (b & 0x7F) * mul;
            if ((b & 0x80) == 0) { ok = 1; break; }
            mul *= 128;
        }
        if (!ok) break;
        int total = pos + rem;
        if (s_rx_len < total) break;

        uint8_t ptype = (uint8_t)(hdr >> 4);
        if (ptype == 3 && rem >= 2) { /* PUBLISH */
            int tlen = ((int)s_rx_buf[pos] << 8) | s_rx_buf[pos + 1];
            int p_off = pos + 2 + tlen;
            if ((hdr & 0x06) != 0) p_off += 2; /* QoS > 0 packet id */
            if (tlen > 0 && tlen < 256 && p_off <= total) {
                char topic[256];
                memcpy(topic, s_rx_buf + pos + 2, (size_t)tlen);
                topic[tlen] = '\0';
                int plen = total - p_off;
                char payload[1024];
                if (plen >= (int)sizeof(payload)) plen = (int)sizeof(payload) - 1;
                if (plen > 0) memcpy(payload, s_rx_buf + p_off, (size_t)plen);
                payload[plen] = '\0';
                mqtt_handle_publish(topic, payload, plen);
            }
        }

        int left = s_rx_len - total;
        if (left > 0) memmove(s_rx_buf, s_rx_buf + total, (size_t)left);
        s_rx_len = left;
    }
}

static int connect_tcp_timeout(const char* host, uint16_t port, int timeout_ms) {
    struct addrinfo hints, *res = NULL;
    char port_str[16];
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;
    snprintf(port_str, sizeof(port_str), "%u", (unsigned)port);
    if (getaddrinfo(host, port_str, &hints, &res) != 0 || !res) return -1;

    SOCKET sk = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (sk == INVALID_SOCKET) { freeaddrinfo(res); return -1; }

    u_long nb = 1;
    ioctlsocket(sk, FIONBIO, &nb);
    int rc = connect(sk, res->ai_addr, (int)res->ai_addrlen);
    freeaddrinfo(res);

    if (rc != 0) {
        int err = WSAGetLastError();
        if (err != WSAEWOULDBLOCK && err != WSAEINPROGRESS) {
            closesocket(sk);
            return -1;
        }
        fd_set wfds;
        FD_ZERO(&wfds);
        FD_SET(sk, &wfds);
        struct timeval tv;
        tv.tv_sec = timeout_ms / 1000;
        tv.tv_usec = (timeout_ms % 1000) * 1000;
        if (select(0, NULL, &wfds, NULL, &tv) <= 0) {
            closesocket(sk);
            return -1;
        }
        int so_err = 0;
        int so_len = (int)sizeof(so_err);
        getsockopt(sk, SOL_SOCKET, SO_ERROR, (char*)&so_err, &so_len);
        if (so_err != 0) {
            closesocket(sk);
            return -1;
        }
    }
    s_sock = sk;
    return 0;
}

typedef struct { char host[128]; uint16_t port; } BrokerEntry;

static int load_mqtt_brokers(BrokerEntry* out, int max_n) {
    int n = 0;
    FILE* f = fopen("bag2jp_online_servers.txt", "r");
    if (f) {
        char line[256];
        while (fgets(line, sizeof(line), f) && n < max_n) {
            char* p = line;
            while (*p == ' ' || *p == '\t') p++;
            if (strncmp(p, "mqtt ", 5) != 0) continue;
            p += 5;
            while (*p == ' ' || *p == '\t') p++;
            char* nl = strpbrk(p, "\r\n");
            if (nl) *nl = '\0';
            char* col = strchr(p, ':');
            if (!col) continue;
            *col = '\0';
            safe_copy(out[n].host, sizeof(out[n].host), p);
            out[n].port = (uint16_t)atoi(col + 1);
            if (out[n].host[0] && out[n].port > 0) n++;
        }
        fclose(f);
    }
    if (n == 0) {
        safe_copy(out[n].host, sizeof(out[n].host), "broker.hivemq.com"); out[n++].port = 1883;
        safe_copy(out[n].host, sizeof(out[n].host), "broker.emqx.io"); out[n++].port = 1883;
        safe_copy(out[n].host, sizeof(out[n].host), "test.mosquitto.org"); out[n++].port = 1883;
    }
    return n;
}

/* =========================== Legacy TCP Line Parser =========================== */

static void parse_room_list(const char* line) {
    s_state.room_count = 0;
    const char* p = strstr(line, "\"rooms\":[");
    if (!p) return;
    p += 9;
    while (*p && s_state.room_count < LOBBY_MAX_ROOMS) {
        const char* obj_start = strchr(p, '{');
        if (!obj_start) break;
        const char* obj_end = strchr(obj_start, '}');
        if (!obj_end) break;
        size_t len = (size_t)(obj_end - obj_start + 1);
        if (len < 512) {
            char item[512];
            memcpy(item, obj_start, len);
            item[len] = '\0';
            LobbyRoomSummary* r = &s_state.rooms[s_state.room_count++];
            memset(r, 0, sizeof(*r));
            json_get_int(item, "room_id", &r->room_id);
            json_get_str(item, "room_name", r->room_name, sizeof(r->room_name));
            json_get_str(item, "host_name", r->host_name, sizeof(r->host_name));
            json_get_int(item, "players", &r->players);
            json_get_int(item, "max_players", &r->max_players);
            json_get_str(item, "state", r->state, sizeof(r->state));
        }
        p = obj_end + 1;
    }
}

static void handle_line(const char* line) {
    char type[32] = {0};
    if (!json_get_str(line, "type", type, sizeof(type))) return;

    if (strcmp(type, "room_list") == 0) {
        parse_room_list(line);
    } else if (strcmp(type, "room_state") == 0) {
        s_state.in_room = 1;
        json_get_int(line, "room_id", &s_state.room_id);
        json_get_str(line, "room_name", s_state.room_name, sizeof(s_state.room_name));
        json_get_str(line, "host_name", s_state.host_name, sizeof(s_state.host_name));
        json_get_int(line, "host_avatar", &s_state.host_avatar);
        json_get_str(line, "guest_name", s_state.guest_name, sizeof(s_state.guest_name));
        json_get_int(line, "guest_avatar", &s_state.guest_avatar);
        json_get_int(line, "guest_ready", &s_state.guest_ready);
        json_get_str(line, "state", s_state.room_state, sizeof(s_state.room_state));
    } else if (strcmp(type, "chat_msg") == 0) {
        char sender[32] = {0}, text[208] = {0};
        json_get_str(line, "sender", sender, sizeof(sender));
        json_get_str(line, "text", text, sizeof(text));
        append_chat(sender, text);
    } else if (strcmp(type, "match_start") == 0) {
        s_state.match_started = 1;
        json_get_str(line, "room_code", s_state.match_room_code, sizeof(s_state.match_room_code));
    } else if (strcmp(type, "error") == 0) {
        json_get_str(line, "msg", s_state.last_error, sizeof(s_state.last_error));
    }
}

/* =========================== Public API =========================== */

int bag2jp_lobby_connect(const char* host, uint16_t port) {
    static int s_wsa_ok = 0;
    if (!s_wsa_ok) {
        WSADATA wsa;
        if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) return -1;
        s_wsa_ok = 1;
    }
    bag2jp_lobby_disconnect();
    memset(&s_state, 0, sizeof(s_state));
    s_rx_len = 0;

    const char* env_host = getenv("BAG2JP_LOBBY_HOST");
    s_use_mqtt = (env_host && env_host[0]) ? 0 : 1;

    if (!s_use_mqtt) {
        if (connect_tcp_timeout(host, port, 2500) != 0) {
            safe_copy(s_state.last_error, sizeof(s_state.last_error), "Connection failed");
            return -1;
        }
        s_state.connected = 1;
        return 0;
    }

    BrokerEntry brokers[8];
    int nb = load_mqtt_brokers(brokers, 8);
    for (int i = 0; i < nb; ++i) {
        if (connect_tcp_timeout(brokers[i].host, brokers[i].port, 2500) == 0) {
            s_state.connected = 1;
            char cid[32];
            uint32_t rnd = (uint32_t)(GetTickCount64() ^ (uintptr_t)&s_state ^ (uint32_t)GetCurrentProcessId());
            snprintf(cid, sizeof(cid), "bag2jp_%08x", rnd);
            if (mqtt_send_connect(cid) == 0 && mqtt_send_sub("bag2jp/lobby/v1/rooms/+") == 0) {
                s_last_ping_ms = GetTickCount64();
                return 0;
            }
            bag2jp_lobby_disconnect();
        }
    }
    safe_copy(s_state.last_error, sizeof(s_state.last_error), "No MQTT broker reachable");
    return -1;
}

void bag2jp_lobby_disconnect(void) {
    if (s_use_mqtt && s_state.connected && s_state.in_room) {
        (void)bag2jp_lobby_leave_room();
    }
    if (s_sock != INVALID_SOCKET) {
        closesocket(s_sock);
        s_sock = INVALID_SOCKET;
    }
    s_state.connected = 0;
    s_state.in_room = 0;
}

void bag2jp_lobby_poll(void) {
    if (s_sock == INVALID_SOCKET || !s_state.connected) return;

    if (s_use_mqtt) {
        uint64_t now = GetTickCount64();
        if (now - s_last_ping_ms >= 15000) {
            s_last_ping_ms = now;
            mqtt_send_ping();
            mqtt_prune_stale_rooms();
        }
        if (s_state.in_room && s_state.is_host && (now - s_last_hb_ms >= LOBBY_ROOM_HB_MS)) {
            mqtt_publish_room_state();
        }
    }

    for (;;) {
        int space = (int)sizeof(s_rx_buf) - 1 - s_rx_len;
        if (space <= 0) { s_rx_len = 0; space = (int)sizeof(s_rx_buf) - 1; }
        int n = recv(s_sock, (char*)s_rx_buf + s_rx_len, space, 0);
        if (n > 0) {
            s_rx_len += n;
            if (s_use_mqtt) {
                mqtt_process_rx();
            } else {
                s_rx_buf[s_rx_len] = '\0';
                char* start = (char*)s_rx_buf;
                char* nl;
                while ((nl = strchr(start, '\n')) != NULL) {
                    *nl = '\0';
                    handle_line(start);
                    start = nl + 1;
                }
                int rem = (int)((char*)s_rx_buf + s_rx_len - start);
                if (rem > 0) memmove(s_rx_buf, start, (size_t)rem);
                s_rx_len = rem;
            }
        } else if (n == 0) {
            if (s_sock != INVALID_SOCKET) { closesocket(s_sock); s_sock = INVALID_SOCKET; }
            s_state.connected = 0;
            s_state.in_room = 0;
            safe_copy(s_state.last_error, sizeof(s_state.last_error), "Disconnected");
            break;
        } else {
            int err = WSAGetLastError();
            if (err != WSAEWOULDBLOCK) {
                if (s_sock != INVALID_SOCKET) { closesocket(s_sock); s_sock = INVALID_SOCKET; }
                s_state.connected = 0;
                s_state.in_room = 0;
                safe_copy(s_state.last_error, sizeof(s_state.last_error), "Socket error");
            }
            break;
        }
    }
}

const LobbyClientState* bag2jp_lobby_state(void) {
    return &s_state;
}

int bag2jp_lobby_list_rooms(void) {
    if (s_use_mqtt) return s_state.connected ? 0 : -1; /* rooms arrive live via retained subscription */
    return send_line("{\"type\":\"list_rooms\"}\n");
}

int bag2jp_lobby_create_room(const char* room_name, const char* player_name, int avatar_id, uint32_t content_id) {
    s_state.is_host = 1;
    s_state.chat_count = 0;
    s_state.match_started = 0;
    safe_copy(s_local_name, sizeof(s_local_name), player_name ? player_name : "Host");
    if (!s_use_mqtt) {
        char buf[256];
        snprintf(buf, sizeof(buf),
                 "{\"type\":\"create_room\",\"room_name\":\"%s\",\"player_name\":\"%s\",\"avatar_id\":%d,\"content_id\":%u}\n",
                 room_name ? room_name : "Room", s_local_name, avatar_id, content_id);
        return send_line(buf);
    }
    if (!s_state.connected) return -1;
    s_state.in_room = 1;
    s_state.room_id = (int)((GetTickCount64() ^ (uint64_t)GetCurrentProcessId()) & 0x7FFF) + 100;
    safe_copy(s_state.room_name, sizeof(s_state.room_name), room_name ? room_name : "Room");
    safe_copy(s_state.host_name, sizeof(s_state.host_name), s_local_name);
    s_state.host_avatar = avatar_id;
    s_state.guest_name[0] = '\0';
    s_state.guest_avatar = 0;
    s_state.guest_ready = 0;
    safe_copy(s_state.room_state, sizeof(s_state.room_state), "Waiting");
    s_room_content_id = content_id;

    char ev_topic[96];
    snprintf(ev_topic, sizeof(ev_topic), "bag2jp/lobby/v1/room/%d/ev", s_state.room_id);
    (void)mqtt_send_sub(ev_topic);
    mqtt_publish_room_state();
    return 0;
}

int bag2jp_lobby_join_room(int room_id, const char* player_name, int avatar_id, uint32_t content_id) {
    s_state.is_host = 0;
    s_state.chat_count = 0;
    s_state.match_started = 0;
    safe_copy(s_local_name, sizeof(s_local_name), player_name ? player_name : "Guest");
    if (!s_use_mqtt) {
        char buf[256];
        snprintf(buf, sizeof(buf),
                 "{\"type\":\"join_room\",\"room_id\":%d,\"player_name\":\"%s\",\"avatar_id\":%d,\"content_id\":%u}\n",
                 room_id, s_local_name, avatar_id, content_id);
        return send_line(buf);
    }
    if (!s_state.connected) return -1;
    s_state.in_room = 1;
    s_state.room_id = room_id;
    safe_copy(s_state.guest_name, sizeof(s_state.guest_name), s_local_name);
    s_state.guest_avatar = avatar_id;
    s_state.guest_ready = 0;

    char ev_topic[96], body[256];
    snprintf(ev_topic, sizeof(ev_topic), "bag2jp/lobby/v1/room/%d/ev", room_id);
    (void)mqtt_send_sub(ev_topic);
    snprintf(body, sizeof(body),
             "{\"type\":\"join\",\"name\":\"%s\",\"avatar\":%d,\"content_id\":%u}",
             s_local_name, avatar_id, content_id);
    return mqtt_send_pub(ev_topic, body, 0);
}

int bag2jp_lobby_leave_room(void) {
    int was_host = s_state.is_host;
    int rid = s_state.room_id;
    s_state.in_room = 0;
    s_state.is_host = 0;
    if (!s_use_mqtt) {
        return send_line("{\"type\":\"leave_room\"}\n");
    }
    if (!s_state.connected || rid <= 0) return 0;
    char ev_topic[96];
    snprintf(ev_topic, sizeof(ev_topic), "bag2jp/lobby/v1/room/%d/ev", rid);
    if (was_host) {
        char rtopic[96];
        snprintf(rtopic, sizeof(rtopic), "bag2jp/lobby/v1/rooms/%d", rid);
        (void)mqtt_send_pub(rtopic, "", 1); /* clear retained room */
    } else {
        char body[128];
        snprintf(body, sizeof(body), "{\"type\":\"leave\",\"name\":\"%s\"}", s_local_name);
        (void)mqtt_send_pub(ev_topic, body, 0);
    }
    (void)mqtt_send_unsub(ev_topic);
    return 0;
}

int bag2jp_lobby_set_ready(int ready) {
    if (!s_use_mqtt) {
        char buf[64];
        snprintf(buf, sizeof(buf), "{\"type\":\"set_ready\",\"ready\":%s}\n", ready ? "true" : "false");
        return send_line(buf);
    }
    if (!s_state.connected || !s_state.in_room) return -1;
    s_state.guest_ready = ready ? 1 : 0;
    char ev_topic[96], body[64];
    snprintf(ev_topic, sizeof(ev_topic), "bag2jp/lobby/v1/room/%d/ev", s_state.room_id);
    snprintf(body, sizeof(body), "{\"type\":\"ready\",\"ready\":%d}", ready ? 1 : 0);
    return mqtt_send_pub(ev_topic, body, 0);
}

int bag2jp_lobby_set_avatar(int avatar_id) {
    if (!s_use_mqtt) {
        char buf[64];
        snprintf(buf, sizeof(buf), "{\"type\":\"set_avatar\",\"avatar_id\":%d}\n", avatar_id);
        return send_line(buf);
    }
    if (!s_state.connected || !s_state.in_room) return -1;
    if (s_state.is_host) {
        s_state.host_avatar = avatar_id;
        mqtt_publish_room_state();
        return 0;
    }
    s_state.guest_avatar = avatar_id;
    char ev_topic[96], body[96];
    snprintf(ev_topic, sizeof(ev_topic), "bag2jp/lobby/v1/room/%d/ev", s_state.room_id);
    snprintf(body, sizeof(body), "{\"type\":\"avatar\",\"role\":\"guest\",\"avatar\":%d}", avatar_id);
    return mqtt_send_pub(ev_topic, body, 0);
}

int bag2jp_lobby_send_chat(const char* text) {
    if (!text || !text[0]) return -1;
    if (!s_use_mqtt) {
        char buf[300];
        snprintf(buf, sizeof(buf), "{\"type\":\"chat_msg\",\"text\":\"%s\"}\n", text);
        return send_line(buf);
    }
    if (!s_state.connected || !s_state.in_room) return -1;
    char ev_topic[96], body[320];
    snprintf(ev_topic, sizeof(ev_topic), "bag2jp/lobby/v1/room/%d/ev", s_state.room_id);
    snprintf(body, sizeof(body), "{\"type\":\"chat\",\"sender\":\"%s\",\"text\":\"%s\"}", s_local_name, text);
    return mqtt_send_pub(ev_topic, body, 0);
}

int bag2jp_lobby_start_match(void) {
    if (!s_use_mqtt) {
        return send_line("{\"type\":\"start_match\"}\n");
    }
    if (!s_state.connected || !s_state.in_room || !s_state.is_host) return -1;
    if (!s_state.guest_ready) {
        safe_copy(s_state.last_error, sizeof(s_state.last_error), "GUEST IS NOT READY!");
        return -1;
    }
    uint32_t rnd = (uint32_t)(GetTickCount64() ^ ((uint64_t)s_state.room_id << 16));
    snprintf(s_state.match_room_code, sizeof(s_state.match_room_code), "B2_%08X", rnd);
    safe_copy(s_state.room_state, sizeof(s_state.room_state), "Playing");
    mqtt_publish_room_state();
    char ev_topic[96], body[128];
    snprintf(ev_topic, sizeof(ev_topic), "bag2jp/lobby/v1/room/%d/ev", s_state.room_id);
    snprintf(body, sizeof(body), "{\"type\":\"match_start\",\"room_code\":\"%s\"}", s_state.match_room_code);
    return mqtt_send_pub(ev_topic, body, 0);
}

int bag2jp_lobby_finish_match(void) {
    s_state.match_started = 0;
    s_state.guest_ready = 0;
    if (!s_use_mqtt) {
        return send_line("{\"type\":\"finish_match\"}\n");
    }
    if (!s_state.connected || !s_state.in_room) return 0;
    if (s_state.is_host) {
        safe_copy(s_state.room_state, sizeof(s_state.room_state), "Waiting");
        mqtt_publish_room_state();
    }
    return 0;
}
