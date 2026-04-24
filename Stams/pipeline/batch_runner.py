"""SentinelVision — Batch GPU Runner.

Collects face crops from all N cameras and runs ArcFace on the
full batch in one GPU call instead of N sequential calls.

TODO: Implement in Phase 15.
"""
from __future__ import annotations
