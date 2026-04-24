"""SentinelVision — GPU Device Manager.

Manages CUDA device selection and model loading. Raises ModelLoadError
if no CUDA device is found.
"""
from __future__ import annotations

import torch
from core.exceptions import ModelLoadError
from core.logger import get_logger
from config import settings

logger = get_logger(__name__)

def check_cuda_available() -> torch.device:
    """Verify CUDA is available and return the target device."""
    if not torch.cuda.is_available():
        logger.error("CUDA is not available. GPU acceleration is required.")
        raise ModelLoadError("No CUDA device found. SentinelVision requires an NVIDIA GPU.")
    
    device_id = settings.GPU_DEVICE
    
    if device_id >= torch.cuda.device_count():
        logger.warning(f"Requested GPU device {device_id} not found. Falling back to device 0.")
        device_id = 0

    device = torch.device(f"cuda:{device_id}")
    gpu_name = torch.cuda.get_device_name(device_id)
    logger.info(f"Using GPU: {gpu_name} (cuda:{device_id})")
    
    return device

def get_device() -> torch.device:
    """Get the active PyTorch device."""
    return check_cuda_available()
