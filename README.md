# SentinelVision

> Real-time multi-camera surveillance system with AI-powered person detection, face recognition, crowd behaviour analysis, and instant alerting.

---

## What It Does

SentinelVision processes **N simultaneous camera feeds** (USB webcam, RTSP IP cameras, or Android phone cameras via IP Webcam) and applies a layered AI pipeline in real time:

1. **Person Detection** — YOLOv8n identifies every person in frame (class 0 only).
2. **Multi-Object Tracking** — ByteTrack assigns persistent track IDs across frames so each individual is followed continuously.
3. **Face Recognition** — ArcFace extracts 512-dimensional face embeddings and matches them against a pre-loaded target photo using cosine similarity.
4. **Crowd Behaviour Analysis** — DeepFace reads dominant emotions per face; if the ratio of alert emotions (fear, anger, disgust) exceeds 40%, the crowd state flips to **AGITATED**.
5. **Pose & Movement Analysis** — MediaPipe body landmarks are compared frame-to-frame to detect running or panic movement.
6. **Instant Alerts** — When a target match or crowd anomaly is detected, SentinelVision plays an audible alarm, highlights the camera feed with a red pulsing border, and auto-switches the React dashboard to a focus view.

A live **React dashboard** connects over WebSocket and displays all camera feeds in an adaptive grid (normal mode) or a focus view (alert mode). The system supports **1 to N cameras** — add or remove cameras simply by editing your `.env` file.

### Android Phone Cameras

Use any Android phone as a camera source via apps like **IP Webcam** or **DroidCam**. Set the RTSP URL in your `.env`:
```
CAMERA_SOURCES=http://192.168.1.101:8080/video,http://192.168.1.102:8080/video,http://192.168.1.103:8080/video,http://192.168.1.104:8080/video
```

---

## Architecture Diagram

```
N Camera Inputs (RTSP / USB / Android IP Webcam)
        │
        ▼
CameraStream threads (one per camera) ──► FrameBuffer (thread-safe ring buffer)
        │
        ▼
Preprocessor (resize 640×640, BGR→RGB, normalize)
        │
        ▼
YOLOv8n ──► person bounding boxes [x1,y1,x2,y2] + confidence
        │
        ▼
ByteTrack ──► tracked persons with stable track_id
        │
        ├── every 3rd frame ──► ArcFace embedding ──► cosine similarity ──► ALERT?
        │
        ├── every 3rd frame ──► MediaPipe Pose ──► landmark velocity ──► movement state
        │
        └── every 5th frame ──► DeepFace Emotion ──► crowd state (CALM / AGITATED)
        │
        ▼
AlertManager ──► pygame sound + WebSocket push
        │
        ▼
FastAPI /ws ──► React Dashboard (adaptive grid │ focus view)
```

---

## Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| GPU | NVIDIA GTX 1660 (6 GB) | RTX 3080 (10 GB) / Jetson Orin |
| CUDA | 11.0+ | 12.0+ |
| RAM | 16 GB | 32 GB |
| CPU | 6-core / 12-thread | 8-core / 16-thread |
| Cameras | 1 source (USB / Android phone) | N sources (Android phones / PoE IP cameras) |
| Storage | 50 GB SSD | 256 GB NVMe |

---

## Software Requirements

| Software | Version |
|----------|---------|
| Python | 3.10+ |
| Node.js | 18+ |
| NVIDIA Driver | 525+ |
| CUDA Toolkit | 11.8+ |
| Docker | 24+ (optional) |
| docker-compose | 2.20+ (optional) |
| Android app | IP Webcam / DroidCam (for phone cameras) |

---

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-org/sentinelvision.git
cd sentinelvision/Stams
```

### 2. Create environment file
```bash
cp .env.example .env
# Edit .env — set CAMERA_SOURCES as a comma-separated list of your camera URLs
```

### 3. Install Python dependencies
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 4. Download AI models
```bash
python scripts/download_models.py
```
This downloads YOLOv8n weights and ArcFace model files into `models/`.

### 5. Install frontend dependencies
```bash
cd frontend
npm install
cd ..
```

---

## Running the System

### Backend only
```bash
uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend only
```bash
cd frontend
npm run dev
```

### Full stack (Docker)
```bash
docker compose up --build
```

---

## Configuration (.env Reference)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CAMERA_SOURCES` | str | `0` | Comma-separated camera sources. Integer for USB, URL for RTSP/IP Webcam. Example: `0,http://192.168.1.101:8080/video` |
| `DETECTION_CONF` | float | `0.4` | YOLOv8 confidence threshold |
| `MATCH_THRESHOLD` | float | `0.6` | ArcFace cosine similarity threshold for face match |
| `PANIC_VELOCITY_THRESHOLD` | float | `15.0` | MediaPipe landmark velocity threshold for panic detection |
| `AGITATED_RATIO` | float | `0.4` | Emotion ratio above which crowd is AGITATED |
| `ALERT_COOLDOWN_SEC` | int | `10` | Minimum seconds between repeated alerts |
| `GPU_DEVICE` | int | `0` | CUDA device index |
| `USE_FP16` | bool | `true` | Use FP16 half-precision inference |
| `API_HOST` | str | `0.0.0.0` | FastAPI bind host |
| `API_PORT` | int | `8000` | FastAPI bind port |
| `LOG_LEVEL` | str | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_DIR` | str | `storage/logs` | Directory for log files |
| `FRAME_WIDTH` | int | `640` | YOLO input width |
| `FRAME_HEIGHT` | int | `640` | YOLO input height |
| `TRACK_THRESH` | float | `0.5` | ByteTrack tracking threshold |
| `TRACK_BUFFER` | int | `30` | ByteTrack track buffer (frames) |
| `MATCH_THRESH` | float | `0.8` | ByteTrack association threshold |
| `MAX_CAMERAS` | int | `16` | Maximum cameras the system will accept |

---

## API Reference

### WebSocket — `ws://localhost:8000/ws`

Streams JSON packets at ~30 fps. Camera array is dynamic (1 to N entries):

```json
{
  "cameras": [
    {
      "id": 0,
      "frame": "<base64 encoded JPEG>",
      "person_count": 12,
      "crowd_state": "CALM",
      "alert": false
    },
    {
      "id": 1,
      "frame": "<base64 encoded JPEG>",
      "person_count": 5,
      "crowd_state": "AGITATED",
      "alert": true
    }
  ],
  "total_cameras": 4,
  "alert_active": true,
  "alert_camera": 1,
  "target_track_id": 47
}
```

### REST Endpoints

| Method | Path | Description | Request | Response |
|--------|------|-------------|---------|----------|
| GET | `/health` | Health check | — | `{"status": "ok"}` |
| GET | `/status` | System status | — | `{"cameras": 4, "gpu": "RTX 3060", "alert_active": false}` |
| POST | `/upload-target` | Upload target face photo | `multipart/form-data` image | `{"status": "ok", "embedding_shape": [512]}` |
| DELETE | `/clear-target` | Remove target embedding | — | `{"status": "cleared"}` |

---

## Performance Tuning Guide

### Frame Skip Strategy

| Module | Frequency | Rationale |
|--------|-----------|-----------|
| YOLOv8 | Every frame | Detection must be continuous |
| ByteTrack | Every frame | Tracking relies on every detection |
| ArcFace | Every 3rd frame | Face embeddings are expensive; faces don't change fast |
| MediaPipe Pose | Every 3rd frame | Velocity needs temporal samples, not every frame |
| DeepFace Emotion | Every 5th frame | Emotions shift slowly; most expensive module |

### Optimisation Checklist

1. **TensorRT export** — Convert YOLOv8n to `.engine` for 3-4× speedup (`scripts/export_tensorrt.py`).
2. **FP16 inference** — Set `USE_FP16=true` in `.env` for all GPU models.
3. **Batch face crops** — All N cameras' face crops are batched into one GPU call via `pipeline/batch_runner.py`.
4. **Capture at 1080p, infer at 640×640** — Raw frames stay full-res for face cropping; only YOLO input is resized.
5. **Pin models to GPU** — All models are loaded once at startup and stay in VRAM.
6. **Ring buffer** — `FrameBuffer` uses `collections.deque(maxlen=2)` to prevent memory growth.

---

## Known Hard Problems and Workarounds

| Problem | Workaround |
|---------|------------|
| ArcFace fails on small or blurry faces | Skip embedding if face crop is < 80×80 pixels |
| DeepFace is slow (~200ms per face) | Run only every 5th frame; batch multiple faces |
| ByteTrack loses ID during full occlusion > 1s | Increase `TRACK_BUFFER` to 60 at the cost of more memory |
| RTSP/IP Webcam stream reconnection | CameraStream auto-reconnects after 5 failed reads with exponential backoff |
| Android phone WiFi latency | Use 5GHz WiFi band; keep phones plugged in for power |
| Multiple pygame sound overlaps | AlertManager enforces cooldown window (`ALERT_COOLDOWN_SEC`) |
| GPU OOM with many cameras | Reduce `det_size` to (320,320) or limit `MAX_CAMERAS` |
| WebSocket backpressure | Drop frames if send queue exceeds 3 entries |

---

## Project Structure

```
Stams/
│
├── .env                        # Environment variables (not committed)
├── .env.example                # Template for .env
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
├── README.md
├── PHASES.md
│
├── config.py                   # Pydantic BaseSettings configuration
├── main.py                     # Entry point
│
├── core/
│   ├── __init__.py
│   ├── logger.py               # Structured logging
│   ├── gpu_manager.py          # GPU device management
│   ├── frame_buffer.py         # Thread-safe ring buffer
│   └── exceptions.py           # Custom exception classes
│
├── cameras/
│   ├── __init__.py
│   ├── stream.py               # Single camera stream thread
│   └── manager.py              # Multi-camera manager (N cameras)
│
├── detection/
│   ├── __init__.py
│   ├── detector.py             # YOLOv8 person detector
│   └── preprocessor.py         # Frame resize & normalization
│
├── tracking/
│   ├── __init__.py
│   └── tracker.py              # ByteTrack wrapper
│
├── face/
│   ├── __init__.py
│   ├── embedder.py             # ArcFace embedding extraction
│   ├── matcher.py              # Cosine similarity matching
│   └── target_store.py         # Target photo storage
│
├── analysis/
│   ├── __init__.py
│   ├── expression.py           # DeepFace emotion analysis
│   └── pose.py                 # MediaPipe pose & movement
│
├── pipeline/
│   ├── __init__.py
│   ├── orchestrator.py         # Main processing loop
│   ├── frame_processor.py      # Per-camera frame pipeline
│   └── batch_runner.py         # Batched GPU inference
│
├── alerts/
│   ├── __init__.py
│   └── alert_manager.py        # Alert state & sound playback
│
├── api/
│   ├── __init__.py
│   ├── server.py               # FastAPI app & WebSocket
│   ├── routes.py               # REST endpoints
│   └── schemas.py              # Pydantic response models
│
├── frontend/
│   ├── package.json
│   └── src/
│       ├── App.jsx
│       ├── components/
│       │   ├── CameraGrid.jsx  # Adaptive N-camera grid
│       │   ├── CameraFeed.jsx
│       │   ├── AlertBanner.jsx
│       │   └── FocusView.jsx
│       └── hooks/
│           └── useWebSocket.js
│
├── models/                     # AI model weights (not committed)
│   ├── yolov8n.pt
│   └── arcface/
│
├── targets/                    # Target face photos
├── storage/
│   ├── embeddings/             # Persisted face embeddings
│   ├── snapshots/              # Alert snapshots
│   └── logs/                   # Rotating log files
│
├── assets/
│   └── alert.wav               # Alert sound file
│
├── scripts/
│   ├── download_models.py
│   ├── test_cameras.py
│   └── benchmark_gpu.py
│
└── tests/
    ├── test_stream.py
    ├── test_detector.py
    ├── test_tracker.py
    ├── test_embedder.py
    ├── test_matcher.py
    ├── test_expression.py
    ├── test_pose.py
    ├── test_alert_manager.py
    └── test_api.py
```

---

## Phase Status

See [PHASES.md](PHASES.md) for the full 25-phase build plan and current progress.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
