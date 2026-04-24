"""SentinelVision — Main Orchestration Loop.

Ties all modules together — reads frames from all N cameras, feeds
each through frame_processor, draws boxes, encodes as base64 JPEG,
and pushes to broadcast queue.

TODO: Implement in Phase 17.
"""
from __future__ import annotations
