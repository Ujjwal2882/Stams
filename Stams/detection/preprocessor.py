"""SentinelVision — Frame Preprocessor.

Resizes raw frames to 640x640 for YOLO input while keeping the
original frame for face cropping at full resolution.
"""
from __future__ import annotations

import cv2
import numpy as np
from typing import Tuple

from config import settings

def preprocess(frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Resizes raw frames to the configured YOLO input size while keeping
    the original frame.
    
    Args:
        frame: The raw numpy array frame.
        
    Returns:
        A tuple of (resized_frame, original_frame). 
        The original frame is not mutated.
    """
    if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
        raise ValueError("Invalid frame provided for preprocessing.")
        
    # Create a copy to guarantee immutability
    original_frame = frame.copy()
    
    target_size = (settings.FRAME_WIDTH, settings.FRAME_HEIGHT)
    
    # Resize to target dimensions
    resized_frame = cv2.resize(original_frame, target_size, interpolation=cv2.INTER_LINEAR)
    
    return resized_frame, original_frame
