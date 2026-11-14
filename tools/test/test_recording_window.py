"""A recording window is pinned temporarily, never another process or forever."""
import unittest

from tools.test.recording_window import RecordingWindow, WindowApi
from unittest.mock import Mock, patch


class FakeWindows:
    """Small Win32 boundary; handles and processes deliberately differ."""

    def __init__(self) -> None:
        self.owners = {100: 700, 200: 800}
        self.front = 200
        self.pinned = False
        self.bounds = (10, 20, 640, 480)
        self.cover = False
        self.allow_focus = True
        self.allow_pin = True
        self.calls = []
        self.tags = set()

    def owner(self, hwnd: int) -> int:
        return self.owners.get(hwnd, 0)

    def owned(self, hwnd: int) -> list[int]:
        return []

    def visible(self, hwnd: int) -> bool:
        return hwnd in self.owners

    def minimized(self, hwnd: int) -> bool:
        return False

    def topmost(self, hwnd: int) -> bool:
        return self.pinned

    def foreground(self) -> int:
        return self.front

    def rect(self, hwnd: int) -> tuple[int, int, int, int]:
        return self.bounds

    def covered(self, hwnd: int, rect: tuple[int, int, int, int]) -> bool:
        return self.cover

    def pin(self, hwnd: int, enabled: bool) -> None:
        self.calls.append(("pin", hwnd, enabled))
        self.pinned = enabled
        if not self.allow_pin:
            raise OSError("pin failed after partial change")

    def focus(self, hwnd: int) -> None:
        self.calls.append(("focus", hwnd))
        if self.allow_focus:
            self.front = hwnd

    def tag(self, hwnd: int, key: str) -> None:
        self.tags.add((hwnd, key))

    def tagged(self, hwnd: int, key: str) -> bool:
        return (hwnd, key) in self.tags

    def untag(self, hwnd: int, key: str) -> None:
        self.tags.discard((hwnd, key))


class PopupWindows(FakeWindows):
    """Simulate Windows topmost propagation through an ownership chain."""

    def __init__(self) -> None:
        self.states = {100: False, 101: False, 102: True}
        super().__init__()
        self.owners.update({101: 700, 102: 700})
        self.parents = {101: 100, 102: 101}

    @property
    def pinned(self) -> bool:
        return self.states[100]

    @pinned.setter
    def pinned(self, enabled: bool) -> None:
        self.states[100] = enabled

    def owned(self, hwnd: int) -> list[int]:
        return [101, 102]  # API supplies owners before descendants

    def topmost(self, hwnd: int) -> bool:
        return self.states.get(hwnd, False)

    def pin(self, hwnd: int, enabled: bool) -> None:
        self.calls.append(("pin", hwnd, enabled))
        self.states[hwnd] = enabled
        for child in self.parents:
            parent = self.parents[child]
            while parent:
                if parent == hwnd:
                    self.states[child] = enabled
                    break
                parent = self.parents.get(parent)


class RecordingWindowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.api = FakeWindows()

    def test_any_selected_process_is_pinned_only_inside_context(self) -> None:
        with RecordingWindow(100, 700, api=self.api) as window:
            self.assertTrue(self.api.pinned)
            self.assertEqual(self.api.front, 100)
            window.check()
        self.assertFalse(self.api.pinned)
        self.assertEqual(self.api.front, 200)

    def test_exception_restores_topmost_and_foreground(self) -> None:
        with self.assertRaisesRegex(ValueError, "capture failed"):
            with RecordingWindow(100, 700, api=self.api):
                raise ValueError("capture failed")
        self.assertFalse(self.api.pinned)
        self.assertEqual(self.api.front, 200)

    def test_existing_topmost_is_preserved(self) -> None:
        self.api.pinned = True
        with RecordingWindow(100, 700, api=self.api):
            pass
        self.assertTrue(self.api.pinned)
        self.assertNotIn(("pin", 100, False), self.api.calls)

    def test_foreground_denial_allows_only_topmost_uncovered_capture(self) -> None:
        self.api.allow_focus = False
        with RecordingWindow(100, 700, api=self.api) as window:
            self.assertFalse(window.focus_acquired)
            self.assertTrue(self.api.pinned)
            self.assertEqual(self.api.front, 200)
            self.api.cover = True
            with self.assertRaisesRegex(RuntimeError, "covered"):
                window.check()
        self.assertFalse(self.api.pinned)

    def test_wrong_pid_does_not_touch_any_window(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "identity"):
            with RecordingWindow(100, 701, api=self.api):
                pass
        self.assertEqual(self.api.calls, [])

    def test_partial_pin_failure_attempts_rollback(self) -> None:
        self.api.allow_pin = False
        with self.assertRaisesRegex(OSError, "pin failed"):
            with RecordingWindow(100, 700, api=self.api):
                pass
        self.assertIn(("pin", 100, False), self.api.calls)

    def test_interrupt_during_activation_rolls_back(self) -> None:
        def interrupted(hwnd: int) -> None:
            raise KeyboardInterrupt()
        self.api.focus = interrupted
        with self.assertRaises(KeyboardInterrupt):
            with RecordingWindow(100, 700, api=self.api):
                pass
        self.assertFalse(self.api.pinned)

    def test_user_focus_change_is_not_overwritten_on_cleanup(self) -> None:
        self.api.owners[300] = 900
        with RecordingWindow(100, 700, api=self.api):
            self.api.front = 300
        self.assertEqual(self.api.front, 300)
        self.assertFalse(self.api.pinned)

    def test_recycled_handle_is_not_modified_on_cleanup(self) -> None:
        with RecordingWindow(100, 700, api=self.api):
            self.api.owners[100] = 999
            self.api.calls.clear()
        self.assertEqual(self.api.calls, [])

    def test_same_pid_recycled_handle_cannot_inherit_window_cookie(self) -> None:
        with RecordingWindow(100, 700, api=self.api) as window:
            self.api.tags.remove((100, window.key))
            self.api.calls.clear()
            with self.assertRaisesRegex(RuntimeError, "identity"):
                window.check()
        self.assertEqual(self.api.calls, [])
        self.assertFalse(self.api.tags)

    def test_popups_restore_in_owner_order_and_survive_missing_target(self) -> None:
        for destroy_target in (False, True):
            with self.subTest(destroy_target=destroy_target):
                api = PopupWindows()
                expected = dict(api.states)
                with RecordingWindow(100, 700, api=api) as window:
                    if destroy_target:
                        del api.owners[100]
                        api.tags.remove((100, window.key))
                        api.parents[101] = None
                for hwnd in (101, 102):
                    self.assertEqual(api.states[hwnd], expected[hwnd])
                self.assertFalse(api.tags)

    def test_native_popup_inventory_sorts_owners_before_descendants(self) -> None:
        api = WindowApi.__new__(WindowApi)
        api.windows = lambda: [102, 101, 100]
        api.user = Mock()
        api.user.GetWindow.side_effect = lambda hwnd, kind: {102: 101, 101: 100}.get(hwnd)
        self.assertEqual(api.owned(100), [101, 102])

    def test_overlap_geometry_change_and_unpin_fail_closed(self) -> None:
        for change in ("overlap", "geometry", "unpin"):
            with self.subTest(change=change):
                self.api = FakeWindows()
                with RecordingWindow(100, 700, api=self.api) as window:
                    if change == "overlap":
                        self.api.cover = True
                    elif change == "geometry":
                        self.api.bounds = (11, 20, 640, 480)
                    else:
                        self.api.pinned = False
                    with self.assertRaises(RuntimeError):
                        window.check()

    def test_wgc_mode_allows_overlap_and_move_without_pinning_but_rejects_resize_minimize_or_close(self) -> None:
        self.api = FakeWindows()
        self.api.iconic = False
        self.api.minimized = lambda hwnd: self.api.iconic
        with RecordingWindow(100, 700, api=self.api, require_uncovered=False) as window:
            self.assertFalse(self.api.pinned)
            self.assertEqual(self.api.front, 200)
            self.assertEqual(self.api.calls, [])
            self.api.cover = True
            self.api.bounds = (180, 90, 640, 480)
            window.check()
            for change, value in (("resized", (180, 90, 800, 600)),
                                  ("minimized", True),
                                  ("hidden", False),
                                  ("recycled", 999)):
                with self.subTest(change=change):
                    self.api.bounds = (180, 90, 640, 480)
                    self.api.iconic = False
                    self.api.__dict__.pop("visible", None)
                    self.api.owners[100] = 700
                    if change == "resized":
                        self.api.bounds = value
                    elif change == "minimized":
                        self.api.iconic = value
                    elif change == "hidden":
                        self.api.visible = lambda hwnd: False
                    else:
                        self.api.owners[100] = value
                    with self.assertRaises(RuntimeError):
                        window.check()
            self.api.bounds = (180, 90, 640, 480)
            self.api.iconic = False
            self.api.__dict__.pop("visible", None)
            self.api.owners[100] = 700
        self.assertFalse(self.api.tags)
        self.assertFalse(self.api.pinned)
        self.assertEqual(self.api.front, 200)
        summary = window.summary()
        self.assertFalse(summary["require_uncovered"])
        self.assertFalse(summary["passed"])  # error set by the injected RuntimeError checks

    def test_wgc_mode_same_pid_recycled_handle_cannot_inherit_cookie_and_enter_failure_cleans_tag(self) -> None:
        self.api = FakeWindows()
        with RecordingWindow(100, 700, api=self.api, require_uncovered=False) as window:
            self.api.tags.clear()
            with self.assertRaises(RuntimeError):
                window.check()
        self.assertFalse(self.api.tags)
        original_check = RecordingWindow.check
        with patch.object(RecordingWindow, "check", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                RecordingWindow(100, 700, api=self.api, require_uncovered=False).__enter__()
        self.assertFalse(self.api.tags)
        self.assertIs(RecordingWindow.check, original_check)


if __name__ == "__main__":
    unittest.main()
