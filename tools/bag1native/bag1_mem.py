"""Read/write PSX RAM of the native BAG1 recompiled runtime (BustAGroove_Recompiled.exe).

Usage:
  py -3.13 tools/bag1native/bag1_mem.py base
  py -3.13 tools/bag1native/bag1_mem.py read <psx_addr_hex> <count> [w|h|b]
  py -3.13 tools/bag1native/bag1_mem.py write <psx_addr_hex> <value_hex> [w|h|b]

The RAM base is found by matching the SCUS_942.63 text section (loaded at
0x80010000 from file offset 0x800) against committed private memory.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import struct
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.workflow import configured  # noqa: E402

PROCESS_NAME = "BustAGroove_Recompiled"
SCUS = configured.path("inputs.bag1_exe_image")
RAM_SIZE = 0x200000
PROBE_FILE_OFF = 0x800 + 0x100  # inside main exe text
PROBE_PSX = 0x80010100

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
PROCESS_VM_READ, PROCESS_VM_WRITE, PROCESS_VM_OPERATION, PROCESS_QUERY_INFORMATION = 0x10, 0x20, 0x8, 0x400


class MBI(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
                ("AllocationProtect", wt.DWORD), ("PartitionId", wt.WORD), ("RegionSize", ctypes.c_size_t),
                ("State", wt.DWORD), ("Protect", wt.DWORD), ("Type", wt.DWORD)]


k32.OpenProcess.restype = wt.HANDLE
k32.VirtualQueryEx.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.POINTER(MBI), ctypes.c_size_t]
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
k32.WriteProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]


def find_pid() -> int:
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          f"(Get-Process -Name {PROCESS_NAME} -ErrorAction Stop | Select -First 1).Id"],
                         capture_output=True, text=True, check=True).stdout.strip()
    return int(out)


class Bag1Mem:
    def __init__(self, pid: int | None = None):
        self.pid = pid or find_pid()
        access = PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION | PROCESS_QUERY_INFORMATION
        self.h = k32.OpenProcess(access, False, self.pid)
        if not self.h:
            raise OSError(ctypes.get_last_error(), "OpenProcess failed")
        self.base = self._find_base()

    def _raw_read(self, addr: int, size: int) -> bytes | None:
        buf = ctypes.create_string_buffer(size)
        got = ctypes.c_size_t()
        if not k32.ReadProcessMemory(self.h, ctypes.c_void_p(addr), buf, size, ctypes.byref(got)) or got.value != size:
            return None
        return buf.raw

    def _find_base(self) -> int:
        needle = SCUS.read_bytes()[PROBE_FILE_OFF:PROBE_FILE_OFF + 64]
        mbi = MBI()
        addr = 0
        hits = []
        while k32.VirtualQueryEx(self.h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
            size = mbi.RegionSize
            # memory.c keeps `static uint8_t ram[]` in the exe image; heap copies are rewind/savestates.
            if mbi.State == 0x1000 and mbi.Type == 0x1000000 and mbi.Protect in (0x04, 0x08, 0x40):
                data = self._raw_read(mbi.BaseAddress, size)
                if data:
                    pos = data.find(needle)
                    while pos >= 0:
                        base = mbi.BaseAddress + pos - (PROBE_PSX & 0x1FFFFF)
                        hits.append(base)
                        pos = data.find(needle, pos + 1)
            addr = (mbi.BaseAddress or 0) + size
            if addr >= 0x7FFFFFFFFFFF:
                break
        scus = SCUS.read_bytes()
        checks = [(0x80018000, 0x8800), (0x80040000, 0x30800)]
        hits = [b for b in hits
                if all(self._raw_read(b + (psx & 0x1FFFFF), 64) == scus[off:off + 64] for psx, off in checks)]
        if len(hits) != 1:
            raise RuntimeError(f"PSX RAM base ambiguous or missing: {[hex(h) for h in hits]}")
        return hits[0]

    def host(self, psx: int) -> int:
        return self.base + (psx & 0x1FFFFF)

    def read(self, psx: int, size: int) -> bytes:
        data = self._raw_read(self.host(psx), size)
        if data is None:
            raise OSError(ctypes.get_last_error(), f"read {psx:#x} failed")
        return data

    def write(self, psx: int, data: bytes) -> None:
        got = ctypes.c_size_t()
        if not k32.WriteProcessMemory(self.h, ctypes.c_void_p(self.host(psx)), data, len(data), ctypes.byref(got)):
            raise OSError(ctypes.get_last_error(), f"write {psx:#x} failed")

    def u32(self, psx: int) -> int: return struct.unpack("<I", self.read(psx, 4))[0]
    def s16(self, psx: int) -> int: return struct.unpack("<h", self.read(psx, 2))[0]
    def u16(self, psx: int) -> int: return struct.unpack("<H", self.read(psx, 2))[0]
    def u8(self, psx: int) -> int: return self.read(psx, 1)[0]


FMT = {"w": ("<I", 4), "h": ("<H", 2), "b": ("<B", 1)}


def main(argv: list[str]) -> int:
    mem = Bag1Mem()
    cmd = argv[0] if argv else "base"
    if cmd == "base":
        print(f"pid {mem.pid} ram_base {mem.base:#x}")
    elif cmd == "read":
        addr, count = int(argv[1], 16), int(argv[2])
        fmt, size = FMT[argv[3] if len(argv) > 3 else "w"]
        vals = struct.unpack("<" + fmt[1] * count, mem.read(addr, size * count))
        print(" ".join(f"{v:0{size*2}x}" for v in vals))
    elif cmd == "write":
        addr, val = int(argv[1], 16), int(argv[2], 16)
        fmt, _ = FMT[argv[3] if len(argv) > 3 else "w"]
        mem.write(addr, struct.pack(fmt, val))
        print("ok")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
