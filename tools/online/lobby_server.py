#!/usr/bin/env python3
"""Lightweight 1v1 lobby server for BAG2JP online mode (JSON-lines over TCP)."""

from __future__ import annotations

import asyncio
import json
import secrets
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ClientSession:
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    player_name: str = ""
    avatar_id: int = 0
    content_id: int = 0
    room_id: int | None = None

    async def send(self, payload: dict[str, Any]) -> None:
        data = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
        self.writer.write(data)
        await self.writer.drain()


@dataclass
class Room:
    room_id: int
    room_name: str
    host: ClientSession
    guest: ClientSession | None = None
    guest_ready: bool = False
    state: str = "Waiting"  # Waiting | Playing
    room_code: str = field(default_factory=lambda: f"B2_{secrets.token_hex(4).upper()}")

    def to_summary(self) -> dict[str, Any]:
        return {
            "room_id": self.room_id,
            "room_name": self.room_name,
            "host_name": self.host.player_name,
            "players": 2 if self.guest is not None else 1,
            "max_players": 2,
            "state": self.state,
        }

    def to_state(self) -> dict[str, Any]:
        return {
            "type": "room_state",
            "room_id": self.room_id,
            "room_name": self.room_name,
            "host_name": self.host.player_name,
            "host_avatar": self.host.avatar_id,
            "guest_name": self.guest.player_name if self.guest else "",
            "guest_avatar": self.guest.avatar_id if self.guest else 0,
            "guest_ready": self.guest_ready,
            "state": self.state,
        }


class LobbyServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 47400) -> None:
        self.host = host
        self.port = port
        self._next_room_id = 1
        self._rooms: dict[int, Room] = {}
        self._server: asyncio.AbstractServer | None = None

    async def start(self) -> int:
        self._server = await asyncio.start_server(self._handle_client, self.host, self.port)
        sock = self._server.sockets[0]
        self.port = sock.getsockname()[1]
        return self.port

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        client = ClientSession(reader=reader, writer=writer)
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                try:
                    msg = json.loads(line.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    await client.send({"type": "error", "code": "bad_json", "msg": "Invalid JSON"})
                    continue
                if not isinstance(msg, dict):
                    await client.send({"type": "error", "code": "bad_msg", "msg": "Expected object"})
                    continue
                await self._dispatch(client, msg)
        except (ConnectionResetError, BrokenPipeError):
            pass
        finally:
            await self._leave_room(client)
            writer.close()

    async def _dispatch(self, client: ClientSession, msg: dict[str, Any]) -> None:
        mtype = msg.get("type")
        if mtype == "list_rooms":
            rooms = [r.to_summary() for r in self._rooms.values()]
            await client.send({"type": "room_list", "rooms": rooms})
        elif mtype == "create_room":
            await self._create_room(client, msg)
        elif mtype == "join_room":
            await self._join_room(client, msg)
        elif mtype == "leave_room":
            await self._leave_room(client)
        elif mtype == "set_ready":
            await self._set_ready(client, bool(msg.get("ready", False)))
        elif mtype == "set_avatar":
            await self._set_avatar(client, int(msg.get("avatar_id", 0)))
        elif mtype == "chat_msg":
            await self._chat_msg(client, str(msg.get("text", "")))
        elif mtype == "start_match":
            await self._start_match(client)
        elif mtype == "finish_match":
            await self._finish_match(client)
        else:
            await client.send({"type": "error", "code": "unknown_type", "msg": f"Unknown: {mtype}"})

    async def _create_room(self, client: ClientSession, msg: dict[str, Any]) -> None:
        await self._leave_room(client)
        room_name = str(msg.get("room_name", "")).strip()[:40] or "Room"
        player_name = str(msg.get("player_name", "")).strip()[:24] or "Host"
        client.player_name = player_name
        client.avatar_id = int(msg.get("avatar_id", 0))
        client.content_id = int(msg.get("content_id", 0))

        rid = self._next_room_id
        self._next_room_id += 1
        room = Room(room_id=rid, room_name=room_name, host=client)
        self._rooms[rid] = room
        client.room_id = rid
        print(f"[lobby] create_room room_id={rid} host={player_name} avatar={client.avatar_id}", flush=True)
        await client.send(room.to_state())

    async def _join_room(self, client: ClientSession, msg: dict[str, Any]) -> None:
        await self._leave_room(client)
        rid = int(msg.get("room_id", 0))
        room = self._rooms.get(rid)
        if room is None:
            await client.send({"type": "error", "code": "not_found", "msg": "Room not found"})
            return
        if room.guest is not None or room.state != "Waiting":
            await client.send({"type": "error", "code": "room_full", "msg": "Room is full"})
            return

        client.player_name = str(msg.get("player_name", "")).strip()[:24] or "Guest"
        client.avatar_id = int(msg.get("avatar_id", 0))
        client.content_id = int(msg.get("content_id", 0))
        room.guest = client
        room.guest_ready = False
        client.room_id = rid
        print(f"[lobby] join_room room_id={rid} guest={client.player_name} avatar={client.avatar_id}", flush=True)
        await self._broadcast_room(room, room.to_state())

    async def _leave_room(self, client: ClientSession) -> None:
        rid = client.room_id
        if rid is None:
            return
        client.room_id = None
        room = self._rooms.get(rid)
        if room is None:
            return
        if room.host is client:
            if room.guest is not None:
                room.guest.room_id = None
                await self._safe_send(
                    room.guest, {"type": "error", "code": "host_left", "msg": "Host closed room"}
                )
            self._rooms.pop(rid, None)
        elif room.guest is client:
            room.guest = None
            room.guest_ready = False
            room.state = "Waiting"
            await self._safe_send(room.host, room.to_state())

    async def _set_ready(self, client: ClientSession, ready: bool) -> None:
        room = self._rooms.get(client.room_id or -1)
        if room is None or room.guest is not client:
            await client.send({"type": "error", "code": "not_guest", "msg": "Only guest can ready"})
            return
        room.guest_ready = ready
        print(f"[lobby] set_ready room_id={room.room_id} guest={client.player_name} ready={ready}", flush=True)
        await self._broadcast_room(room, room.to_state())

    async def _set_avatar(self, client: ClientSession, avatar_id: int) -> None:
        client.avatar_id = avatar_id
        room = self._rooms.get(client.room_id or -1)
        if room is not None:
            await self._broadcast_room(room, room.to_state())

    async def _chat_msg(self, client: ClientSession, text: str) -> None:
        room = self._rooms.get(client.room_id or -1)
        if room is None:
            await client.send({"type": "error", "code": "not_in_room", "msg": "Join a room first"})
            return
        clean = text.strip()[:200]
        if not clean:
            return
        print(f"[lobby] chat_msg room_id={room.room_id} sender={client.player_name} text={clean!r}", flush=True)
        await self._broadcast_room(
            room,
            {
                "type": "chat_msg",
                "sender": client.player_name,
                "text": clean,
                "ts": int(time.time()),
            },
        )

    async def _start_match(self, client: ClientSession) -> None:
        room = self._rooms.get(client.room_id or -1)
        if room is None or room.host is not client:
            await client.send({"type": "error", "code": "not_host", "msg": "Only host can start"})
            return
        if room.guest is None:
            print(f"[lobby] start_match REJECTED room_id={room.room_id} reason=no_guest", flush=True)
            await client.send({"type": "error", "code": "no_guest", "msg": "Waiting for opponent"})
            return
        if not room.guest_ready:
            print(f"[lobby] start_match REJECTED room_id={room.room_id} reason=not_ready", flush=True)
            await client.send({"type": "error", "code": "not_ready", "msg": "Guest is not ready"})
            return
        if room.host.content_id != room.guest.content_id:
            print(f"[lobby] start_match REJECTED room_id={room.room_id} reason=content_mismatch", flush=True)
            await client.send(
                {"type": "error", "code": "content_mismatch", "msg": "Content ID mismatch"}
            )
            return

        room.state = "Playing"
        print(f"[lobby] match_start ACCEPTED room_id={room.room_id} room_code={room.room_code}", flush=True)
        await self._broadcast_room(room, room.to_state())
        await self._broadcast_room(
            room,
            {"type": "match_start", "room_code": room.room_code, "transport": "internet"},
        )

    async def _finish_match(self, client: ClientSession) -> None:
        room = self._rooms.get(client.room_id or -1)
        if room is None:
            return
        if room.state != "Waiting":
            room.state = "Waiting"
            room.guest_ready = False
            print(f"[lobby] finish_match room_id={room.room_id} -> Waiting (returned to room)", flush=True)
            await self._broadcast_room(room, room.to_state())

    async def _broadcast_room(self, room: Room, payload: dict[str, Any]) -> None:
        await self._safe_send(room.host, payload)
        if room.guest is not None:
            await self._safe_send(room.guest, payload)

    @staticmethod
    async def _safe_send(client: ClientSession, payload: dict[str, Any]) -> None:
        try:
            await client.send(payload)
        except (ConnectionResetError, BrokenPipeError):
            pass


async def main() -> None:
    server = LobbyServer(host="0.0.0.0", port=47400)
    port = await server.start()
    print(f"BAG2JP LobbyServer listening on 0.0.0.0:{port}")
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
