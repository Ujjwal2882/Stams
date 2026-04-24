"""SentinelVision — Camera Stream.

Opens one USB, RTSP, or Android IP Webcam source in a background thread
and exposes the latest frame via get_frame() without blocking.

Gracefully handles Docker / headless environments where no camera hardware
is available by entering a "fallback-only" mode instead of spamming
reconnection attempts.
"""
from __future__ import annotations

import os
import cv2
import time
import logging
import threading
import numpy as np
from typing import Optional, Union

from core.logger import get_logger
from core.frame_buffer import FrameBuffer

logger = get_logger(__name__)


def _is_hardware_index(source: Union[int, str]) -> bool:
    """Return True when *source* refers to a local device index (0, 1, …)."""
    return isinstance(source, int)


def _camera_hardware_available(index: int) -> bool:
    """Quick probe: can we open the device at *index*?

    The test opens and immediately releases the capture so we don't hold
    the device.  Returns False inside Docker / headless hosts where
    /dev/videoN does not exist.
    """
    cap = cv2.VideoCapture(index)
    ok = cap.isOpened()
    cap.release()
    return ok


class CameraStream:
    """Background thread to read frames from a camera source continuously.

    When the source is a local device index (e.g. ``0``) **and** the device
    is not reachable (common inside Docker), the stream enters *fallback
    mode*: it serves a static "NO SIGNAL" frame and does **not** retry,
    avoiding the flood of OpenCV warnings in the container logs.

    Network sources (RTSP URLs, IP Webcam URLs) still get exponential-
    backoff reconnection because they are expected to come online later.
    """

    def __init__(self, camera_id: int, source: Union[int, str]):
        self.camera_id = camera_id

        # Normalise: "0" → 0
        if isinstance(source, str) and source.isdigit():
            self.source: Union[int, str] = int(source)
        else:
            self.source = source

        # --- Detect whether hardware is available before opening -----------
        self._fallback_only = False  # True → serve static frame, no retry

        if _is_hardware_index(self.source):
            if not _camera_hardware_available(self.source):
                logger.warning(
                    f"Camera {self.camera_id}: local device index "
                    f"{self.source} is NOT available (Docker / headless). "
                    f"Entering fallback mode — serving placeholder frames."
                )
                self._fallback_only = True

        # Only open the real capture if we're not in fallback mode
        self.cap: Optional[cv2.VideoCapture] = None
        if not self._fallback_only:
            self.cap = cv2.VideoCapture(self.source)

        self.buffer = FrameBuffer(maxlen=2)

        self.running = False
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.failed_reads = 0
        self.max_failed_reads = 5

    # ----- public API ------------------------------------------------------

    def start(self) -> None:
        """Start the background thread."""
        if self._fallback_only:
            # Push one fallback frame immediately so get_frame() never
            # returns None, then start the light-weight fallback loop.
            self.buffer.write(self._generate_fallback_frame())
            self.running = True
            self.thread.start()
            logger.info(
                f"Camera {self.camera_id} started in FALLBACK mode "
                f"(no hardware at source {self.source})."
            )
            return

        if self.cap and not self.cap.isOpened():
            logger.error(
                f"Camera {self.camera_id} at {self.source} failed to open "
                f"initially — will retry in background thread."
            )

        self.running = True
        self.thread.start()
        logger.info(f"Camera {self.camera_id} stream started.")

    def get_frame(self) -> Optional[np.ndarray]:
        """Return the latest frame from the buffer without blocking."""
        return self.buffer.read()

    def stop(self) -> None:
        """Stop the background thread and release resources."""
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=2.0)
        if self.cap is not None:
            self.cap.release()
        logger.info(f"Camera {self.camera_id} stream stopped.")

    # ----- internal --------------------------------------------------------

    def _reconnect(self) -> None:
        """Attempt to reconnect to the camera source with exponential backoff.

        Only called for network sources or hardware that was once available.
        """
        logger.warning(f"Camera {self.camera_id} attempting to reconnect...")
        if self.cap is not None:
            self.cap.release()

        backoff = 1
        while self.running:
            self.cap = cv2.VideoCapture(self.source)
            if self.cap.isOpened():
                logger.info(f"Camera {self.camera_id} reconnected successfully.")
                self.failed_reads = 0
                return

            logger.debug(
                f"Camera {self.camera_id} reconnect failed. "
                f"Waiting {backoff}s..."
            )
            time.sleep(backoff)
            backoff = min(backoff * 2, 30)

    def _generate_fallback_frame(self) -> np.ndarray:
        """Generates a dummy 'NO SIGNAL' frame to display when hardware fails."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Add slight static pattern
        noise = np.random.randint(0, 50, (480, 640, 3), dtype=np.uint8)
        frame = cv2.add(frame, noise)

        cv2.putText(frame, f"CAM {self.camera_id} - NO SIGNAL", (100, 240),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
        cv2.putText(frame, "HARDWARE UNREACHABLE", (130, 280),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        return frame

    def _update(self) -> None:
        """Main loop for the background thread."""

        # ---------- Fallback-only mode (no hardware) -----------------------
        if self._fallback_only:
            while self.running:
                # Refresh the static-noise frame periodically so the UI
                # looks "alive" rather than frozen.
                self.buffer.write(self._generate_fallback_frame())
                time.sleep(1.0)  # 1 fps is plenty for a placeholder
            return

        # ---------- Normal mode (real capture) -----------------------------
        while self.running:
            if self.cap is None or not self.cap.isOpened():
                self.buffer.write(self._generate_fallback_frame())
                self._reconnect()
                continue

            ret, frame = self.cap.read()
            if ret:
                self.failed_reads = 0
                self.buffer.write(frame)
            else:
                self.failed_reads += 1
                logger.debug(
                    f"Camera {self.camera_id} missed frame "
                    f"({self.failed_reads}/{self.max_failed_reads})"
                )

                # Push a fallback frame so the UI doesn't freeze or drop the camera
                self.buffer.write(self._generate_fallback_frame())

                if self.failed_reads >= self.max_failed_reads:
                    logger.error(
                        f"Camera {self.camera_id} reached max failed reads. "
                        f"Reconnecting..."
                    )
                    self._reconnect()
                else:
                    time.sleep(0.01)  # Avoid tight loop on temporary read failure


if __name__ == "__main__":
    # Standalone execution test
    import sys
    logging.basicConfig(level=logging.INFO)

    stream = CameraStream(camera_id=0, source=0)
    stream.start()

    try:
        frames_read = 0
        start_time = time.time()

        while frames_read < 100:
            frame = stream.get_frame()
            if frame is not None:
                print(f"Frame shape: {frame.shape}")
                frames_read += 1
            time.sleep(1/30)  # simulate 30fps reading

        fps = frames_read / (time.time() - start_time)
        print(f"Read {frames_read} frames at ~{fps:.1f} fps")

    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        stream.stop()
