"""SentinelVision — Thread-Safe Frame Buffer.

Ring buffer using collections.deque(maxlen=2) for sharing frames
between camera threads and the processing pipeline.
"""
from __future__ import annotations

import collections
import threading
from typing import Optional
import numpy as np

class FrameBuffer:
    """Thread-safe ring buffer for storing the latest camera frames."""
    
    def __init__(self, maxlen: int = 2):
        self._buffer = collections.deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def write(self, frame: np.ndarray) -> None:
        """Write a new frame to the buffer in a thread-safe manner."""
        with self._lock:
            self._buffer.append(frame)

    def read(self) -> Optional[np.ndarray]:
        """Read the latest frame from the buffer."""
        with self._lock:
            if not self._buffer:
                return None
            return self._buffer[-1]
