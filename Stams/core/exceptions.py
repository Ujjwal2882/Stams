"""SentinelVision — Custom Exception Classes.

All custom exceptions for the project. Importable via:
    from core.exceptions import ModelLoadError, CameraError, ...
"""
from __future__ import annotations

class SentinelError(Exception):
    """Base exception for all SentinelVision errors."""
    pass

class ModelLoadError(SentinelError):
    """Raised when an AI model fails to load (e.g., missing CUDA)."""
    pass

class CameraError(SentinelError):
    """Raised when a camera stream encounters a fatal error."""
    pass

class DetectionError(SentinelError):
    """Raised when the detection module fails."""
    pass

class ConfigError(SentinelError):
    """Raised for invalid configuration setups."""
    pass
