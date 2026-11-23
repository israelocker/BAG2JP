#!/usr/bin/env python3
"""Unit tests for tools/online/lobby_server.py."""

import asyncio
import json
import unittest

from lobby_server import LobbyServer


class LobbyClientHelper:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.reader = reader
        self.writer = writer

    @classmethod
    async def connect(cls, port: int) -> "LobbyClientHelper":
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        return cls(reader, writer)

    async def send(self, payload: dict) -> None:
        self.writer.write((json.dumps(payload) + "\n").encode("utf-8"))
        await self.writer.drain()

    async def recv(self) -> dict:
        line = await asyncio.wait_for(self.reader.readline(), timeout=2.0)
        return json.loads(line.decode("utf-8"))

    async def close(self) -> None:
        self.writer.close()
        await self.writer.wait_closed()


class TestLobbyServer(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.server = LobbyServer(host="127.0.0.1", port=0)
        self.port = await self.server.start()

    async def asyncTearDown(self) -> None:
        await self.server.stop()

    async def test_room_flow_ready_chat_and_start(self) -> None:
        host = await LobbyClientHelper.connect(self.port)
        guest = await LobbyClientHelper.connect(self.port)
        try:
            await host.send({"type": "create_room", "room_name": "Sala 1v1", "player_name": "Alice", "content_id": 1234})
            st = await host.recv()
            self.assertEqual(st["type"], "room_state")
            self.assertEqual(st["host_name"], "Alice")
            rid = st["room_id"]

            await guest.send({"type": "list_rooms"})
            lst = await guest.recv()
            self.assertEqual(len(lst["rooms"]), 1)
            self.assertEqual(lst["rooms"][0]["players"], 1)

            await guest.send({"type": "join_room", "room_id": rid, "player_name": "Bob", "content_id": 1234})
            st_h = await host.recv()
            st_g = await guest.recv()
            self.assertEqual(st_h["guest_name"], "Bob")
            self.assertFalse(st_g["guest_ready"])

            # Host cannot start before guest is ready
            await host.send({"type": "start_match"})
            err = await host.recv()
            self.assertEqual(err["code"], "not_ready")

            # Chat works inside room
            await guest.send({"type": "chat_msg", "text": "hola!"})
            c_h = await host.recv()
            c_g = await guest.recv()
            self.assertEqual(c_h["sender"], "Bob")
            self.assertEqual(c_g["text"], "hola!")

            # Guest marks ready -> Host can start
            await guest.send({"type": "set_ready", "ready": True})
            st_h = await host.recv()
            st_g = await guest.recv()
            self.assertTrue(st_h["guest_ready"])

            await host.send({"type": "start_match"})
            _ = await host.recv()  # room_state Playing
            _ = await guest.recv()
            m_h = await host.recv()
            m_g = await guest.recv()
            self.assertEqual(m_h["type"], "match_start")
            self.assertEqual(m_h["room_code"], m_g["room_code"])
        finally:
            await host.close()
            await guest.close()

    async def test_content_mismatch_blocks_start(self) -> None:
        host = await LobbyClientHelper.connect(self.port)
        guest = await LobbyClientHelper.connect(self.port)
        try:
            await host.send({"type": "create_room", "room_name": "Test", "player_name": "A", "content_id": 111})
            rid = (await host.recv())["room_id"]
            await guest.send({"type": "join_room", "room_id": rid, "player_name": "B", "content_id": 222})
            await host.recv()
            await guest.recv()
            await guest.send({"type": "set_ready", "ready": True})
            await host.recv()
            await guest.recv()

            await host.send({"type": "start_match"})
            err = await host.recv()
            self.assertEqual(err["code"], "content_mismatch")
        finally:
            await host.close()
            await guest.close()


if __name__ == "__main__":
    unittest.main()
