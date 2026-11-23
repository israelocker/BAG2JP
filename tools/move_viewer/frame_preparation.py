"""GUI-independent, bounded preparation of a selected motion's RGB frames."""
from collections.abc import Callable, Sequence
from threading import Event

import numpy as np


def prepare_frames(keys: Sequence[int], render: Callable[[int], np.ndarray],
                   max_bytes: int, cancel: Event,
                   progress: Callable[[int, int], None]) -> list[np.ndarray] | None:
    """Return complete owned RGB buffers, or discard them when canceled."""
    if type(max_bytes) is not int or max_bytes <= 0:
        raise ValueError('frame preparation budget must be positive')
    frames = []
    used = 0
    for key in keys:
        if cancel.is_set():
            return None
        image = np.asarray(render(key))
        if cancel.is_set():
            return None
        if image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
            raise ValueError('prepared frame must be an RGB uint8 image')
        if used + image.nbytes > max_bytes:
            raise ValueError('selected motion exceeds frame preparation budget')
        image = image.copy(order='C')
        frames.append(image)
        used += image.nbytes
        progress(len(frames), len(keys))
    return None if cancel.is_set() else frames
