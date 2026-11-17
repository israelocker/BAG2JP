"""Minimal GDB remote-protocol client for DuckStation's GDB server.

Sets execution breakpoints, logs each hit with PC, a0 and selected RAM words,
then resumes. Used to measure native BAG2 song-start timing (song start
0x800358bc and the overlay GetlocL gate) against the PSXRecomp runtime.

Usage:
  python tools/test/duck_gdb.py --bp 800358bc --bp 80098730 --read 800892ec \
      --seconds 600 --log _work/sync/duck_gdb.log
"""
import argparse
import socket
import struct
import time


class Gdb:
    def __init__(self, host, port):
        self.s = socket.create_connection((host, port), timeout=5)
        self.buf = b""

    def _recv_packet(self, timeout):
        self.s.settimeout(timeout)
        while True:
            start = self.buf.find(b"$")
            if start >= 0:
                end = self.buf.find(b"#", start)
                if end >= 0 and len(self.buf) >= end + 3:
                    body = self.buf[start + 1:end]
                    self.buf = self.buf[end + 3:]
                    self.s.sendall(b"+")
                    return body.decode("latin-1")
            chunk = self.s.recv(65536)
            if not chunk:
                raise ConnectionError("gdb server closed")
            self.buf += chunk

    def cmd(self, body, timeout=5.0):
        data = body.encode("latin-1")
        csum = sum(data) & 0xFF
        self.s.sendall(b"$" + data + b"#" + f"{csum:02x}".encode())
        return self._recv_packet(timeout)

    def send_no_reply(self, body):
        data = body.encode("latin-1")
        self.s.sendall(b"$" + data + b"#" + f"{sum(data) & 0xFF:02x}".encode())

    def wait_stop(self, timeout):
        return self._recv_packet(timeout)

    def regs(self):
        raw = bytes.fromhex(self.cmd("g").replace("x", "0"))  # 'xx' = unavailable
        return struct.unpack_from(f"<{len(raw) // 4}I", raw)

    def read_u32(self, addr):
        return struct.unpack("<I", bytes.fromhex(self.cmd(f"m{addr:x},4")))[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=2345)
    ap.add_argument("--bp", action="append", default=[], help="hex exec breakpoint")
    ap.add_argument("--read", action="append", default=[], help="hex RAM word to log on hit")
    ap.add_argument("--write", action="append", default=[], help="addr=hexbytes written once at attach")
    ap.add_argument("--seconds", type=float, default=600)
    ap.add_argument("--log", required=True)
    a = ap.parse_args()

    g = Gdb(a.host, a.port)
    g.cmd("?")
    for w in a.write:
        addr, data = w.split("=")
        r = g.cmd(f"M{int(addr, 16):x},{len(data) // 2:x}:{data}")
        print(f"write {addr}={data}: {r} readback={g.cmd(f'm{int(addr, 16):x},{len(data) // 2:x}')}")
    for bp in a.bp:
        r = g.cmd(f"Z0,{int(bp, 16):x},4")
        print(f"bp {bp}: {r}")
    t0 = time.monotonic()
    hits = 0
    with open(a.log, "a", encoding="utf-8") as log:
        log.write(f"# start {time.strftime('%Y-%m-%d %H:%M:%S')} bps={a.bp} reads={a.read}\n")
        while time.monotonic() - t0 < a.seconds:
            g.send_no_reply("c")
            try:
                stop = g.wait_stop(max(1.0, a.seconds - (time.monotonic() - t0)))
            except socket.timeout:
                break
            if not stop.startswith(("T", "S")):
                continue
            r = g.regs()
            # GDB MIPS order: r0..r31, sr, lo, hi, bad, cause, pc
            pc, a0 = r[37], r[4]
            vals = " ".join(f"{x}={g.read_u32(int(x, 16)):#x}" for x in a.read)
            line = f"t={time.monotonic() - t0:9.3f} pc={pc:08x} a0={a0:#x} ra={r[31]:08x} {vals}"
            hits += 1
            log.write(line + "\n")
            log.flush()
    for bp in a.bp:
        g.cmd(f"z0,{int(bp, 16):x},4")
    g.send_no_reply("c")
    g.send_no_reply("D")
    print(f"{hits} hits -> {a.log}")


if __name__ == "__main__":
    main()
