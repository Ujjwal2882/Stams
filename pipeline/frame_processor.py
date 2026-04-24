"""SentinelVision — Per-Camera Frame Processor.

Single function that takes a raw frame + cam_id and runs the full
detection → tracking → face matching → pose → expression pipeline,
respecting frame-skip counters.

TODO: Implement in Phase 16.
"""
from __future__ import annotations
