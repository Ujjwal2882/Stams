"""SentinelVision — Configuration Module.

Pydantic BaseSettings class that reads all values from .env
and exposes them as typed attributes to the whole project.
CAMERA_SOURCES is a comma-separated string supporting 1 to N cameras.
"""
from __future__ import annotations

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Camera Sources
    CAMERA_SOURCES: str = "0"
    MAX_CAMERAS: int = 16

    # Detection
    DETECTION_CONF: float = 0.4

    # Face Matching
    MATCH_THRESHOLD: float = 0.6

    # Pose & Movement
    PANIC_VELOCITY_THRESHOLD: float = 15.0

    # Crowd Behaviour
    AGITATED_RATIO: float = 0.4

    # Alerts
    ALERT_COOLDOWN_SEC: int = 10

    # GPU
    GPU_DEVICE: int = 0
    USE_FP16: bool = True

    # API Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "storage/logs"

    # Frame Dimensions
    FRAME_WIDTH: int = 640
    FRAME_HEIGHT: int = 640

    # ByteTrack
    TRACK_THRESH: float = 0.5
    TRACK_BUFFER: int = 30
    MATCH_THRESH: float = 0.8

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def camera_sources_list(self) -> List[str]:
        """Return the comma-separated CAMERA_SOURCES as a list of strings."""
        if not self.CAMERA_SOURCES:
            return []
        sources = [s.strip() for s in self.CAMERA_SOURCES.split(",") if s.strip()]
        return sources[:self.MAX_CAMERAS]

settings = Settings()
