# SENTINELVISION — BUILD PHASES

> Update status after every coding session.
> Never delete a phase — only change its status.

---

## PHASE 01 — Project scaffold & documentation
**Status:** `[ DONE ]`
**Goal:** Create the full folder structure, README.md, PHASES.md, .env.example, .gitignore, requirements.txt, requirements-dev.txt.
**Files:** README.md · PHASES.md · .env.example · .gitignore · requirements.txt · requirements-dev.txt · all __init__.py stubs
**Acceptance:** `tree Stams/` matches the structure exactly. README renders correctly on GitHub.
**Depends on:** nothing

---

## PHASE 02 — Configuration system
**Status:** `[ DONE ]`
**Goal:** Single pydantic BaseSettings class in config.py reads all values from .env and exposes them as typed attributes. CAMERA_SOURCES is a comma-separated list supporting 1 to N cameras.
**Files:** config.py · .env.example (update with all keys)
**Acceptance:** `from config import settings; print(settings.MATCH_THRESHOLD)` prints 0.6. `settings.camera_sources_list` returns a list of N sources. Missing key raises ValidationError on startup, not mid-run.
**Depends on:** Phase 01

---

## PHASE 03 — Core utilities
**Status:** `[ DONE ]`
**Goal:** Shared infrastructure — logger, GPU manager, frame buffer, custom exceptions — available to all modules.
**Files:** core/logger.py · core/gpu_manager.py · core/frame_buffer.py · core/exceptions.py
**Acceptance:** Logger writes to stdout and rotates file in storage/logs/. gpu_manager raises ModelLoadError if no CUDA device found. FrameBuffer returns None if no frame written yet. All exceptions importable from core.exceptions.
**Depends on:** Phase 02

---

## PHASE 04 — Camera stream (single camera)
**Status:** `[ DONE ]`
**Goal:** CameraStream opens one USB, RTSP, or Android IP Webcam source in a background thread and exposes the latest frame via get_frame() without blocking.
**Files:** cameras/stream.py · tests/test_stream.py
**Acceptance:** Running stream.py standalone opens camera 0 and prints frame shape at ~30fps. get_frame() returns None before first frame arrives. Auto-reconnects if cap.read() fails 5 times.
**Depends on:** Phase 03

---

## PHASE 05 — Camera manager (N cameras)
**Status:** `[ DONE ]`
**Goal:** CameraManager starts N CameraStream instances from config (dynamically from CAMERA_SOURCES), provides get_all_frames() returning dict {cam_id: frame}.
**Files:** cameras/manager.py · tests/test_stream.py (update)
**Acceptance:** manager.get_all_frames() returns N entries matching len(settings.camera_sources_list). Empty sources are skipped gracefully. Manager can be stopped cleanly with manager.stop_all(). Works with 1 camera or 16 cameras.
**Depends on:** Phase 04

---

## PHASE 06 — Frame preprocessor
**Status:** `[ DONE ]`
**Goal:** Resize raw frames to 640×640 for YOLO input while keeping the original frame for face cropping at full resolution.
**Files:** detection/preprocessor.py · tests/test_detector.py (partial)
**Acceptance:** preprocess(frame) returns (resized_640, original_frame). Works on any input resolution. Does not mutate the original.
**Depends on:** Phase 05

---

## PHASE 07 — YOLOv8 person detector
**Status:** `[ PENDING ]`
**Goal:** Wrap YOLOv8n to detect only class 0 (person) and return bounding boxes + confidences from the 640×640 input, remapped to original resolution.
**Files:** detection/detector.py · models/yolov8n.pt · tests/test_detector.py
**Acceptance:** detect(frame) returns (boxes_array, scores_array). boxes are in original frame coordinates. Model loaded once at init, not per call. Confidence threshold from settings.DETECTION_CONF.
**Depends on:** Phase 06

---

## PHASE 08 — ByteTrack multi-object tracker
**Status:** `[ PENDING ]`
**Goal:** Wrap ByteTrack to assign stable track_id per person across frames for one camera feed.
**Files:** tracking/tracker.py · tests/test_tracker.py
**Acceptance:** update(boxes, scores, frame_id) returns list of TrackedPerson(bbox, track_id). Same person keeps same ID across 30-frame occlusion. One tracker instance per camera — test with two trackers simultaneously.
**Depends on:** Phase 07

---

## PHASE 09 — ArcFace face embedder
**Status:** `[ PENDING ]`
**Goal:** Use insightface FaceAnalysis to extract a 512-dim ArcFace embedding from a cropped face image.
**Files:** face/embedder.py · tests/test_embedder.py
**Acceptance:** get_embedding(face_crop) returns numpy array shape (512,) or None if no face detected. Model uses CUDAExecutionProvider. det_size=(640,640). Largest face is returned when multiple faces present.
**Depends on:** Phase 03

---

## PHASE 10 — Face matcher & similarity scoring
**Status:** `[ PENDING ]`
**Goal:** Compute cosine similarity between two embeddings and determine if they match based on configurable threshold.
**Files:** face/matcher.py · tests/test_matcher.py
**Acceptance:** cosine_similarity(emb1, emb2) returns float in [-1, 1]. is_match(emb1, emb2) returns bool using settings.MATCH_THRESHOLD. Both functions handle zero-norm embeddings without division error.
**Depends on:** Phase 09

---

## PHASE 11 — Target photo upload & embedding storage
**Status:** `[ PENDING ]`
**Goal:** Accept a target photo, extract its embedding, and persist it to disk so it survives server restarts.
**Files:** face/target_store.py · targets/ directory · tests/test_embedder.py (update)
**Acceptance:** save_target(image) extracts embedding and writes to storage/embeddings/target.npy. load_target() reads it back as numpy array. Returns None if file does not exist. REST endpoint /upload-target accepts multipart image.
**Depends on:** Phase 10

---

## PHASE 12 — Expression analysis
**Status:** `[ PENDING ]`
**Goal:** Analyse the dominant emotion of a face crop and classify the crowd as CALM or AGITATED.
**Files:** analysis/expression.py · tests/test_expression.py
**Acceptance:** analyze_expression(face_crop) returns one of: happy, fear, angry, neutral, sad, disgust, surprise. Falls back to neutral on exception. compute_crowd_state(emotion_list) returns CALM if alert-emotion ratio < 0.4, AGITATED otherwise. Handles empty list.
**Depends on:** Phase 09

---

## PHASE 13 — Pose & movement analysis
**Status:** `[ PENDING ]`
**Goal:** Extract MediaPipe body landmarks from a person crop and compute inter-frame velocity to detect running or panic movement.
**Files:** analysis/pose.py · tests/test_pose.py
**Acceptance:** analyze_movement(frame, bbox) returns landmark list or None. compute_velocity(prev_landmarks, curr_landmarks) returns float (mean displacement). Values above settings.PANIC_VELOCITY_THRESHOLD flag the person as urgent.
**Depends on:** Phase 06

---

## PHASE 14 — Alert manager
**Status:** `[ PENDING ]`
**Goal:** Centralised alert state — plays sound, records which camera and track_id triggered the alert, exposes alert payload for broadcast.
**Files:** alerts/alert_manager.py · assets/alert.wav · tests/test_alert_manager.py
**Acceptance:** trigger(cam_id, track_id) plays alert.wav exactly once per alert event (no repeat spam within cooldown window from settings.ALERT_COOLDOWN_SEC). get_alert_payload() returns dict matching WebSocket JSON schema. clear() resets alert state.
**Depends on:** Phase 02

---

## PHASE 15 — Batch GPU pipeline
**Status:** `[ PENDING ]`
**Goal:** Collect face crops from all N cameras and run ArcFace on the full batch in one GPU call instead of N sequential calls.
**Files:** pipeline/batch_runner.py · tests/ (benchmark script)
**Acceptance:** process_batch(crops_dict) accepts {cam_id: [face_crop, ...]} and returns {cam_id: [embedding, ...]}. Benchmark shows >2× throughput vs sequential. Falls back to sequential if batch is empty.
**Depends on:** Phase 09

---

## PHASE 16 — Frame processor (per-camera per-frame logic)
**Status:** `[ PENDING ]`
**Goal:** Single function that takes a raw frame + cam_id and runs detection → tracking → face matching → pose → expression, respecting frame-skip counters.
**Files:** pipeline/frame_processor.py
**Acceptance:** process_frame(frame, cam_id, frame_count, target_embedding) returns FrameResult(tracked_persons, crowd_state, alert_triggered). Face match runs on frame_count % 3 == 0. Expression on frame_count % 5 == 0. Pose on frame_count % 3 == 0.
**Depends on:** Phase 07 · Phase 08 · Phase 10 · Phase 12 · Phase 13 · Phase 14

---

## PHASE 17 — Main orchestration loop
**Status:** `[ PENDING ]`
**Goal:** Ties all modules together — reads frames from all N cameras, feeds each through frame_processor, draws boxes, encodes frame as base64 JPEG, and pushes to broadcast queue.
**Files:** pipeline/orchestrator.py · main.py (thin wrapper only)
**Acceptance:** Runs at minimum 15fps on a single camera with YOLOv8 + ArcFace on RTX 3060. No blocking calls inside the loop. Loop exits cleanly on SIGINT.
**Depends on:** Phase 15 · Phase 16

---

## PHASE 18 — FastAPI server & WebSocket broadcast
**Status:** `[ PENDING ]`
**Goal:** FastAPI app with /ws WebSocket endpoint that streams frame data to all connected React clients at ~30fps. Camera array is dynamic (1 to N).
**Files:** api/server.py · api/schemas.py · tests/test_api.py
**Acceptance:** ws:// connection receives valid JSON matching the WebSocket packet schema every ~33ms. Disconnected clients are removed cleanly without crashing the loop. /health REST endpoint returns 200. total_cameras field reflects actual camera count.
**Depends on:** Phase 17

---

## PHASE 19 — REST endpoints
**Status:** `[ PENDING ]`
**Goal:** REST API for target management and system control.
**Files:** api/routes.py · api/schemas.py
**Acceptance:** POST /upload-target accepts multipart/form-data image, saves embedding, returns {status: ok, embedding_shape: [512]}. DELETE /clear-target removes stored embedding. GET /status returns camera count, GPU info, alert state. All routes have pydantic response models.
**Depends on:** Phase 11 · Phase 18

---

## PHASE 20 — React app base + WebSocket hook
**Status:** `[ PENDING ]`
**Goal:** React app skeleton with a useWebSocket hook that connects to the backend and stores the latest frame payload in state.
**Files:** frontend/src/App.jsx · frontend/src/hooks/useWebSocket.js · frontend/package.json
**Acceptance:** App connects to ws://localhost:8000/ws. Hook exposes {cameras, alertActive, alertCamera, targetTrackId, totalCameras}. Reconnects automatically on disconnect. No errors in browser console on first load.
**Depends on:** Phase 18

---

## PHASE 21 — Adaptive N-camera dashboard view
**Status:** `[ PENDING ]`
**Goal:** Display all N camera feeds in an adaptive grid (auto-calculates rows/cols based on camera count). Each cell shows live frame, person count badge, and crowd state badge.
**Files:** frontend/src/components/CameraGrid.jsx · frontend/src/components/CameraFeed.jsx
**Acceptance:** Grid adapts to 1, 2, 3, 4, 6, 9, or more cameras automatically. Person count badge updates per frame. Crowd state badge is green for CALM, amber for AGITATED. Layout is responsive down to 1024px width.
**Depends on:** Phase 20

---

## PHASE 22 — Alert mode & focus view
**Status:** `[ PENDING ]`
**Goal:** When alert_active=true, target camera expands to 70% width with a red pulsing border. Other N-1 cameras move to a right sidebar. Alert banner appears at the top.
**Files:** frontend/src/components/FocusView.jsx · frontend/src/components/AlertBanner.jsx
**Acceptance:** Layout transitions in <300ms using framer-motion. Red border pulses at 1s interval. Alert banner shows camera ID and track ID. Clicking dismiss calls DELETE /clear-target and returns to grid view.
**Depends on:** Phase 21

---

## PHASE 23 — TensorRT optimisation
**Status:** `[ PENDING ]`
**Goal:** Export YOLOv8n to TensorRT engine file and swap the detector to use it. Measure before/after fps.
**Files:** scripts/export_tensorrt.py · detection/detector.py (update)
**Acceptance:** TRT engine file generated at models/yolov8n.engine. Detector auto-uses .engine if present, falls back to .pt. Benchmark shows ≥2× fps improvement on RTX 3060.
**Depends on:** Phase 07

---

## PHASE 24 — Docker & deployment
**Status:** `[ PENDING ]`
**Goal:** Dockerfile and docker-compose.yml so the entire stack (backend + frontend) starts with one command on any NVIDIA host.
**Files:** Dockerfile · docker-compose.yml · .dockerignore
**Acceptance:** docker compose up starts both services. Backend container has GPU access (runtime: nvidia). Frontend served on port 3000, backend on 8000. Volumes mount ./targets and ./storage correctly. docker compose down cleans up without data loss.
**Depends on:** Phase 18 · Phase 22

---

## PHASE 25 — Full test suite & benchmark
**Status:** `[ PENDING ]`
**Goal:** All test files pass. End-to-end latency from frame capture to WebSocket broadcast is under 200ms on RTX 3060.
**Files:** tests/ (all files) · scripts/benchmark_gpu.py
**Acceptance:** pytest runs with 0 failures. benchmark_gpu.py prints per-module latency table. Total pipeline latency printed in ms. README performance section updated with real numbers.
**Depends on:** all previous phases

---

## SESSION LOG

> Append a line here after every coding session.

| Date | Session goal | Phases worked | Files changed | Notes |
|------|-------------|---------------|---------------|-------|
| 2026-04-23 | Project scaffold & documentation | Phase 01 | All scaffold files | Initial project setup, N-camera support |
| 2026-04-23 | Phase 01 Verification | Phase 01 | .env, tests/__init__.py | Cross-checked and verified code-level accuracy. Created missing .env from .env.example and tests/__init__.py stub to ensure module clarity. Phase 1 is strictly COMPLETE. |
| 2026-04-23 | Phase 02 Configuration System | Phase 02 | config.py, PHASES.md | Implemented config.py with Pydantic BaseSettings, mapped .env keys, and added list parsing property for N camera sources. |
| 2026-04-23 | Phase 03 Core Utilities | Phase 03 | core/*.py, PHASES.md | Implemented exceptions, structured rotating logger, GPU manager (with CUDA enforcement), and thread-safe ring buffer. |
| 2026-04-23 | Phase 04 Camera Stream | Phase 04 | cameras/stream.py, tests/test_stream.py, PHASES.md | Implemented `CameraStream` via `cv2.VideoCapture` on a background thread utilizing `FrameBuffer`. Automatically handles timeouts and implements exponential backoff for stream reconnections (useful for wireless Android phone streaming). Created associated unit tests. |
| 2026-04-23 | Phase 05 Camera Manager | Phase 05 | cameras/manager.py, tests/test_stream.py, PHASES.md | Implemented `CameraManager` to initialize and manage `N` `CameraStream` instances dynamically from configuration. Returns aggregated frames dict and gracefully handles empty/dropped sources. Verified via updated `test_stream.py`. |
| 2026-04-23 | Phase 06 Frame Preprocessor | Phase 06 | detection/preprocessor.py, tests/test_detector.py, PHASES.md | Implemented `preprocess(frame)` which copies the raw frame for safety and uses `cv2.resize` to generate a 640x640 (configurable via `settings`) frame for YOLO input. Returns `(resized, original_copy)`. Added robust unit tests in `test_detector.py`. |
