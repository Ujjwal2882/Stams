"""SentinelVision — Camera Manager.

Starts all N CameraStream instances from config and provides
get_all_frames() returning dict {cam_id: frame}.
"""
from __future__ import annotations

import logging
from typing import Dict, Optional
import numpy as np

from config import settings
from cameras.stream import CameraStream
from core.logger import get_logger

logger = get_logger(__name__)

class CameraManager:
    """Manages multiple CameraStream instances dynamically based on config."""

    def __init__(self):
        self.streams: Dict[int, CameraStream] = {}
        
        sources = settings.camera_sources_list
        if not sources:
            logger.warning("No camera sources found in config.")
            return
            
        for i, source in enumerate(sources):
            stream = CameraStream(camera_id=i, source=source)
            self.streams[i] = stream
            logger.info(f"Initialized camera {i} with source {source}")

    def start_all(self) -> None:
        """Start all configured camera streams."""
        for cam_id, stream in self.streams.items():
            stream.start()
        logger.info(f"Started {len(self.streams)} camera streams.")

    def get_all_frames(self) -> Dict[int, np.ndarray]:
        """
        Return the latest frames from all active cameras.
        Empty sources (None frame) are skipped gracefully.
        """
        frames = {}
        for cam_id, stream in self.streams.items():
            frame = stream.get_frame()
            if frame is not None:
                frames[cam_id] = frame
        return frames

    def stop_all(self) -> None:
        """Stop all running camera streams cleanly."""
        for cam_id, stream in self.streams.items():
            stream.stop()
        logger.info("Stopped all camera streams.")
