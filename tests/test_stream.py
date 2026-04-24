"""Tests for cameras/stream.py — CameraStream."""
from __future__ import annotations

import time
import numpy as np
import pytest
from unittest.mock import MagicMock, patch
from cameras.stream import CameraStream

@pytest.fixture
def mock_video_capture():
    with patch("cameras.stream._camera_hardware_available", return_value=True), \
         patch("cameras.stream.cv2.VideoCapture") as mock_cap:
        # Create a mock instance
        instance = mock_cap.return_value
        instance.isOpened.return_value = True

        # Mock read to return a dummy frame
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        instance.read.return_value = (True, dummy_frame)

        yield mock_cap

def test_camera_stream_initialization(mock_video_capture):
    stream = CameraStream(camera_id=0, source="0")
    assert stream.camera_id == 0
    assert stream.source == 0  # Should be converted to int
    assert not stream.running

def test_camera_stream_get_frame_empty(mock_video_capture):
    stream = CameraStream(camera_id=0, source=0)
    assert stream.get_frame() is None

def test_camera_stream_start_and_read(mock_video_capture):
    stream = CameraStream(camera_id=0, source=0)
    stream.start()
    
    # Wait for the thread to read at least one frame
    time.sleep(0.1)
    
    frame = stream.get_frame()
    assert frame is not None
    assert frame.shape == (480, 640, 3)
    
    stream.stop()
    assert not stream.running

def test_camera_stream_auto_reconnect(mock_video_capture):
    # Setup the mock to fail read 5 times
    instance = mock_video_capture.return_value
    
    # 5 failures, then success
    instance.read.side_effect = [(False, None)] * 5 + [(True, np.zeros((480, 640, 3), dtype=np.uint8))]
    
    stream = CameraStream(camera_id=0, source=0)
    stream.start()
    
    # Wait for the reconnect logic to trigger
    time.sleep(0.5)
    
    # Check that release was called during reconnect
    assert instance.release.called
    # Check that VideoCapture was called again (reconnected)
    assert mock_video_capture.call_count >= 2
    
    stream.stop()

from cameras.manager import CameraManager

def test_camera_manager_initialization():
    with patch("cameras.manager.settings") as mock_settings, \
         patch("cameras.stream._camera_hardware_available", return_value=True), \
         patch("cameras.stream.cv2.VideoCapture") as mock_cap:
        mock_cap.return_value.isOpened.return_value = True
        mock_settings.camera_sources_list = ["0", "http://test"]
        manager = CameraManager()
        assert len(manager.streams) == 2
        assert manager.streams[0].source == 0
        assert manager.streams[1].source == "http://test"

def test_camera_manager_start_stop(mock_video_capture):
    with patch("cameras.manager.settings") as mock_settings:
        mock_settings.camera_sources_list = ["0", "1"]
        manager = CameraManager()
        
        manager.start_all()
        for stream in manager.streams.values():
            assert stream.running
            
        manager.stop_all()
        for stream in manager.streams.values():
            assert not stream.running

def test_camera_manager_get_all_frames(mock_video_capture):
    with patch("cameras.manager.settings") as mock_settings:
        mock_settings.camera_sources_list = ["0", "1"]
        manager = CameraManager()
        
        manager.start_all()
        time.sleep(0.2)
        
        frames = manager.get_all_frames()
        assert len(frames) == 2
        assert 0 in frames
        assert 1 in frames
        assert frames[0].shape == (480, 640, 3)
        
        manager.stop_all()
