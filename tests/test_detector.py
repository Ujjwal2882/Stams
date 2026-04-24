"""Tests for detection module."""
from __future__ import annotations

import numpy as np
import pytest

from detection.preprocessor import preprocess
from config import settings

def test_preprocessor_resizes_correctly():
    # Create a dummy 1080p frame (Height, Width, Channels) -> (1080, 1920, 3)
    dummy_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    
    resized, original = preprocess(dummy_frame)
    
    # Original should be untouched and cloned
    assert original.shape == (1080, 1920, 3)
    
    # Resized should match configured settings
    assert resized.shape == (settings.FRAME_HEIGHT, settings.FRAME_WIDTH, 3)
    
    # Original and resized should not be the same object in memory
    assert id(original) != id(resized)
    assert id(original) != id(dummy_frame)

def test_preprocessor_invalid_frame():
    with pytest.raises(ValueError):
        preprocess(None)
        
    with pytest.raises(ValueError):
        preprocess(np.array([]))
