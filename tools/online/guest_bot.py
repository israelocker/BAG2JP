#!/usr/bin/env python3
"""Automated Guest client for validating 2-peer Lobby/Room/Chat/Ready/Start flow."""

import asyncio
import json
import sys


async def run_guest(host: str = "127.0.0.1", port: int = 47400) -> int:
    reader, writer = await asyncio.open_connection(host, port)

    async def send(obj: dict) -> None:
        writer.write((json.dumps(obj) + "\n").encode("utf-8"))
        await writer.drain()

    async def recv() -> dict:
        line = await asyncio.wait_for(reader.readline(), timeout=15.0)
        return json.loads(line.decode("utf-8"))

    # Poll until a room exists (up to 40s)
    rid = None
    for _ in range(80):
        await send({"type": "list_rooms"})
        msg = await recv()
        rooms = msg.get("rooms", [])
        if rooms:
            rid = rooms[0]["room_id"]
            break
        await asyncio.sleep(0.5)

    if rid is None:
        print("guest_bot: no room found", file=sys.stderr)
        return 1

    await send({"type": "join_room", "room_id": rid, "player_name": "GuestP2", "avatar_id": 2, "content_id": 0})
    _ = await recv()  # room_state
    print("guest_bot: joined (NOT ready yet — waiting for T3 negative START test)", flush=True)
    await asyncio.sleep(5.0)

    await send({"type": "chat_msg", "text": "hola host"})
    _ = await recv()  # chat_msg echo
    print("guest_bot: sent chat 'hola host' (T4)", flush=True)
    await asyncio.sleep(5.0)

    await send({"type": "set_ready", "ready": True})
    _ = await recv()  # room_state with guest_ready=True
    print("guest_bot: marked READY (T5)", flush=True)

    # Wait for match_start from Host
    for _ in range(20):
        try:
            msg = await asyncio.wait_for(reader.readline(), timeout=1.0)
            if not msg:
                break
            obj = json.loads(msg.decode("utf-8"))
            if obj.get("type") == "match_start":
                print(f"guest_bot: received match_start room_code={obj.get('room_code')}")
                break
        except asyncio.TimeoutError:
            continue

    writer.close()
    await writer.wait_closed()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run_guest()))
