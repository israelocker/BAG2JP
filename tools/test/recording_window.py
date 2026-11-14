"""Pin only the selected capture window, restoring state even after capture errors.

Works with any application's HWND/PID, not a title or executable name. No hotkeys,
input injection, thread attachment, global Windows setting or PowerToys required.
Foreground/topmost/overlap checks are not a substitute for reviewing the pixels.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
from types import TracebackType
from uuid import uuid4

HWND_TOPMOST, HWND_NOTOPMOST = -1, -2
SWP_NOSIZE, SWP_NOMOVE, SWP_NOACTIVATE, SWP_NOOWNERZORDER = 1, 2, 16, 512
GWL_EXSTYLE, WS_EX_TOPMOST = -20, 8
GW_HWNDPREV, GW_OWNER, DWMWA_CLOAKED = 3, 4, 14
MAX_WINDOWS, MIN_CLIENT_SIZE = 4096, 64


class WindowApi:
    """Small native boundary with explicit pointer-sized HWND signatures."""

    def __init__(self) -> None:
        self.user = ctypes.WinDLL("user32", use_last_error=True)
        self.dwm = ctypes.WinDLL("dwmapi", use_last_error=True)
        signatures = {
            "IsWindowVisible": ([wt.HWND], wt.BOOL),
            "IsIconic": ([wt.HWND], wt.BOOL),
            "GetForegroundWindow": ([], wt.HWND),
            "GetWindowThreadProcessId": ([wt.HWND, ctypes.POINTER(wt.DWORD)], wt.DWORD),
            "GetWindowLongW": ([wt.HWND, ctypes.c_int], wt.LONG),
            "GetWindow": ([wt.HWND, wt.UINT], wt.HWND),
            "GetWindowRect": ([wt.HWND, ctypes.POINTER(wt.RECT)], wt.BOOL),
            "GetClientRect": ([wt.HWND, ctypes.POINTER(wt.RECT)], wt.BOOL),
            "ClientToScreen": ([wt.HWND, ctypes.POINTER(wt.POINT)], wt.BOOL),
            "SetForegroundWindow": ([wt.HWND], wt.BOOL),
            "SetWindowPos": ([wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int,
                              ctypes.c_int, ctypes.c_int, wt.UINT], wt.BOOL),
            "EnumWindows": ([ctypes.c_void_p, wt.LPARAM], wt.BOOL),
            "SetPropW": ([wt.HWND, wt.LPCWSTR, wt.HANDLE], wt.BOOL),
            "GetPropW": ([wt.HWND, wt.LPCWSTR], wt.HANDLE),
            "RemovePropW": ([wt.HWND, wt.LPCWSTR], wt.HANDLE),
        }
        for name, (args, result) in signatures.items():
            function = getattr(self.user, name)
            function.argtypes, function.restype = args, result
        self.dwm.DwmGetWindowAttribute.argtypes = [wt.HWND, wt.DWORD, ctypes.c_void_p, wt.DWORD]
        self.dwm.DwmGetWindowAttribute.restype = wt.LONG

    def owner(self, hwnd: int) -> int:
        """Return zero for a closed window, otherwise its current process ID."""
        pid = wt.DWORD()
        self.user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return pid.value

    def visible(self, hwnd: int) -> bool:
        """Whether Windows marks this window visible."""
        return bool(self.user.IsWindowVisible(hwnd))

    def minimized(self, hwnd: int) -> bool:
        """Do not silently restore/minimize an application as a side effect."""
        return bool(self.user.IsIconic(hwnd))

    def topmost(self, hwnd: int) -> bool:
        """Read only the topmost style bit, never overwrite the other styles."""
        return bool(self.user.GetWindowLongW(hwnd, GWL_EXSTYLE) & WS_EX_TOPMOST)

    def foreground(self) -> int:
        """Return the exact foreground HWND, not just the process ID."""
        return self.user.GetForegroundWindow() or 0

    def rect(self, hwnd: int) -> tuple[int, int, int, int]:
        """Physical client bounds; caller must set per-monitor DPI awareness."""
        rect, point = wt.RECT(), wt.POINT()
        if not self.user.GetClientRect(hwnd, ctypes.byref(rect)) or not self.user.ClientToScreen(
                hwnd, ctypes.byref(point)):
            raise ctypes.WinError(ctypes.get_last_error())
        return point.x, point.y, rect.right & ~1, rect.bottom & ~1

    def pin(self, hwnd: int, enabled: bool) -> None:
        """Change only Z order, without moving, resizing or activating."""
        after = HWND_TOPMOST if enabled else HWND_NOTOPMOST
        flags = SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE | SWP_NOOWNERZORDER
        if not self.user.SetWindowPos(hwnd, after, 0, 0, 0, 0, flags):
            raise ctypes.WinError(ctypes.get_last_error())

    def focus(self, hwnd: int) -> None:
        """Request normal activation; Windows may deny it (no lock bypass)."""
        self.user.SetForegroundWindow(hwnd)

    def tag(self, hwnd: int, key: str) -> None:
        """Private temporary property, destroyed by Windows with the HWND."""
        if not self.user.SetPropW(hwnd, key, 1):
            raise ctypes.WinError(ctypes.get_last_error())

    def tagged(self, hwnd: int, key: str) -> bool:
        """A recycled HWND cannot inherit the original window's cookie."""
        return self.user.GetPropW(hwnd, key) == 1

    def untag(self, hwnd: int, key: str) -> None:
        """Remove only this guard's property, preserving all other properties."""
        if not self.user.RemovePropW(hwnd, key):
            raise ctypes.WinError(ctypes.get_last_error())

    def windows(self) -> list[int]:
        """Enumerate top-level handles without inspecting titles or contents."""
        found = []

        @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
        def visit(hwnd: int, unused: int) -> bool:
            found.append(hwnd)
            return len(found) < MAX_WINDOWS

        self.user.EnumWindows(visit, 0)
        if len(found) >= MAX_WINDOWS:
            raise RuntimeError("window enumeration limit reached")
        return found

    def owned(self, hwnd: int) -> list[int]:
        """Snapshot owned popups too: Windows propagates topmost to them."""
        found = []
        for candidate in self.windows():
            parent = self.user.GetWindow(candidate, GW_OWNER)
            seen = set()
            while parent and parent not in seen:
                seen.add(parent)
                if parent == hwnd:
                    found.append((len(seen), candidate))
                    break
                parent = self.user.GetWindow(parent, GW_OWNER)
        # Restoring a parent to non-topmost also clears its descendants. Restore
        # owners first, then children, irrespective of their current Z order.
        return [candidate for _, candidate in sorted(found)]

    def covered(self, hwnd: int, rect: tuple[int, int, int, int]) -> bool:
        """Conservatively reject visible rectangles above the capture client."""
        x, y, width, height = rect
        above = self.user.GetWindow(hwnd, GW_HWNDPREV)
        seen = set()
        while above:
            if above in seen or len(seen) >= MAX_WINDOWS:
                raise RuntimeError("invalid window Z order")
            seen.add(above)
            if self.visible(above) and not self.minimized(above):
                cloaked, bounds = wt.DWORD(), wt.RECT()
                result = self.dwm.DwmGetWindowAttribute(
                    above, DWMWA_CLOAKED, ctypes.byref(cloaked), ctypes.sizeof(cloaked))
                if result != 0 or not self.user.GetWindowRect(above, ctypes.byref(bounds)):
                    raise RuntimeError("cannot verify window overlap")
                if not cloaked.value and (bounds.left < x + width and bounds.right > x and
                                          bounds.top < y + height and bounds.bottom > y):
                    return True
            above = self.user.GetWindow(above, GW_HWNDPREV)
        return False


def find_window(pid: int, api: WindowApi | None = None) -> int | None:
    """Find an unowned main window of any requested PID, never by title."""
    api = api or WindowApi()
    for hwnd in api.windows():
        if api.owner(hwnd) == pid and api.visible(hwnd) and not api.user.GetWindow(hwnd, GW_OWNER):
            _, _, width, height = api.rect(hwnd)
            if min(width, height) >= MIN_CLIENT_SIZE:
                return hwnd
    return None


class RecordingWindow:
    """Temporarily guard one HWND/PID; rollback is safe if that handle is reused."""

    def __init__(self, hwnd: int, pid: int, api: WindowApi | None = None,
                 require_uncovered: bool = True) -> None:
        self.hwnd, self.pid, self.api = hwnd, pid, api or WindowApi()
        self.require_uncovered = require_uncovered
        self.previous, self.previous_pid = 0, 0
        self.original: list[tuple[int, int, bool]] = []
        self.bounds: tuple[int, int, int, int] | None = None
        self.changed, self.checks = False, 0
        self.error: str | None = None
        self.restore_error: str | None = None
        self.key = f"RecordingWindow.{uuid4().hex}"
        self.marked: list[tuple[int, int]] = []
        self.focus_acquired = False

    def __enter__(self) -> RecordingWindow:
        if not self.pid or self.api.owner(self.hwnd) != self.pid:
            raise RuntimeError("capture window identity changed")
        if not self.api.visible(self.hwnd) or self.api.minimized(self.hwnd):
            raise RuntimeError("capture window is hidden or minimized")
        self.bounds = self.api.rect(self.hwnd)
        if not self.require_uncovered:
            try:
                self.api.tag(self.hwnd, self.key)
                self.marked.append((self.hwnd, self.pid))
                self.check()
            except (OSError, RuntimeError, KeyboardInterrupt, SystemExit) as error:
                self.error = str(error)
                self._restore()
                raise
            return self
        self.previous = self.api.foreground()
        self.previous_pid = self.api.owner(self.previous)
        handles = [self.hwnd, *self.api.owned(self.hwnd)]
        self.original = [(h, self.api.owner(h), self.api.topmost(h)) for h in handles]
        if any(pid != self.pid for _, pid, _ in self.original):
            raise RuntimeError("capture window has a foreign owned popup")
        try:
            for handle, owner, _ in self.original:
                self.api.tag(handle, self.key)
                self.marked.append((handle, owner))
            if self.previous and self.previous not in handles:
                # If UIPI forbids tagging another application's window, simply
                # skip restoring its focus rather than trust a recyclable HWND.
                try:
                    self.api.tag(self.previous, self.key)
                except OSError:
                    self.previous = 0
                else:
                    self.marked.append((self.previous, self.previous_pid))
            self.changed = True  # even a partly failed native call must roll back
            self.api.pin(self.hwnd, True)
            self.api.focus(self.hwnd)
            self.focus_acquired = self.api.foreground() == self.hwnd
            self.check()
        except (OSError, RuntimeError, KeyboardInterrupt, SystemExit) as error:
            self.error = str(error)
            self._restore()
            raise
        return self

    def check(self) -> None:
        """Fail closed instead of recording an unusable, resized or replaced window."""
        self.checks += 1
        problem = None
        if not self._live(self.hwnd, self.pid):
            problem = "capture window identity changed"
        elif not self.api.visible(self.hwnd) or self.api.minimized(self.hwnd):
            problem = "capture window is hidden or minimized"
        elif self.require_uncovered:
            if not self.api.topmost(self.hwnd):
                problem = "capture window lost topmost"
            elif self.api.rect(self.hwnd) != self.bounds:
                problem = "capture window moved or resized"
            elif self.api.covered(self.hwnd, self.bounds):
                problem = "capture window is covered"
        elif self.bounds is not None and self.api.rect(self.hwnd)[2:] != self.bounds[2:]:
            problem = "capture window resized"
        if problem:
            self.error = problem
            raise RuntimeError(problem)

    def _restore(self) -> None:
        changed = self.changed
        self.changed = False
        target_exists = self._live(self.hwnd, self.pid)
        if changed:
            for hwnd, pid, topmost in self.original:
                if self._live(hwnd, pid):
                    try:
                        self.api.pin(hwnd, topmost)
                        if self.api.topmost(hwnd) != topmost:
                            self.restore_error = "cannot restore original topmost state"
                    except OSError as error:
                        self.restore_error = str(error)
        # Do not undo a foreground choice the user made during recording.
        if (target_exists and self.previous and self.previous != self.hwnd and
                self.previous_pid and self.api.foreground() == self.hwnd and
                self._live(self.previous, self.previous_pid)):
            self.api.focus(self.previous)
            if self.api.foreground() != self.previous:
                self.restore_error = "cannot restore previous foreground window"
        for hwnd, pid in self.marked:
            if self._live(hwnd, pid):
                try:
                    self.api.untag(hwnd, self.key)
                except OSError as error:
                    self.restore_error = str(error)
        self.marked.clear()

    def _live(self, hwnd: int, pid: int) -> bool:
        return self.api.owner(hwnd) == pid and self.api.tagged(hwnd, self.key)

    def __exit__(self, kind: type | None, value: BaseException | None,
                 traceback: TracebackType | None) -> bool:
        self._restore()
        if self.restore_error and kind is None:
            raise RuntimeError(f"cannot restore recording window: {self.restore_error}")
        return False

    def summary(self) -> dict[str, object]:
        """Auditable outcome, separate from subjective visual inspection."""
        restored = not self.changed and not self.marked
        return {"hwnd": self.hwnd, "pid": self.pid, "checks": self.checks,
                "require_uncovered": self.require_uncovered,
                "focus_acquired": self.focus_acquired,
                "error": self.error, "restore_error": self.restore_error,
                "pending": not restored,
                "passed": self.checks > 0 and restored and not self.error and not self.restore_error}
