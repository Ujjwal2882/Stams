import asyncio
import base64
import time
import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from cameras.manager import CameraManager

app = FastAPI(title="SentinelVision API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

camera_manager = CameraManager()

# Track server startup time for warmup
_startup_time: float = 0.0


def _make_placeholder_frame(cam_id: int, label: str = "STARTING UP") -> str:
    """Generate a base64-encoded JPEG placeholder frame with a status message."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    # Subtle dark-blue gradient fill
    frame[:, :, 0] = 20  # B
    frame[:, :, 1] = 25  # G
    frame[:, :, 2] = 35  # R
    noise = np.random.randint(0, 15, (480, 640, 3), dtype=np.uint8)
    frame = cv2.add(frame, noise)

    cv2.putText(
        frame, f"CAM {cam_id:02d}", (20, 50),
        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (80, 120, 200), 2, cv2.LINE_AA
    )
    cv2.putText(
        frame, label, (20, 110),
        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (60, 90, 160), 2, cv2.LINE_AA
    )
    cv2.putText(
        frame, "Waiting for first frame...", (20, 160),
        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (50, 70, 100), 1, cv2.LINE_AA
    )

    ret, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
    if ret:
        return f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
    return ""


@app.on_event("startup")
async def startup_event():
    global _startup_time
    camera_manager.start_all()
    _startup_time = time.time()
    # Give camera threads ~500 ms to capture their first frame before serving
    await asyncio.sleep(0.5)


@app.on_event("shutdown")
async def shutdown_event():
    camera_manager.stop_all()


@app.get("/")
async def root():
    return {"status": "SentinelVision API is running", "phase": 18}


@app.get("/health")
async def health():
    active = len(camera_manager.streams)
    return {"status": "ok", "cameras_registered": active}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            frames = camera_manager.get_all_frames()

            cameras_payload = []

            # Iterate over ALL registered streams so even warmup cameras appear
            for cam_id in camera_manager.streams:
                frame = frames.get(cam_id)  # may be None during warmup

                if frame is not None:
                    # Real frame: resize and encode
                    small_frame = cv2.resize(frame, (640, 480))
                    ret, buffer = cv2.imencode(
                        ".jpg", small_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75]
                    )
                    if ret:
                        b64 = base64.b64encode(buffer).decode("utf-8")
                        frame_data = f"data:image/jpeg;base64,{b64}"
                    else:
                        frame_data = _make_placeholder_frame(cam_id, "ENCODE ERROR")
                else:
                    # Camera thread hasn't produced a frame yet → send placeholder
                    frame_data = _make_placeholder_frame(cam_id, "STARTING UP")

                cameras_payload.append({
                    "id": cam_id,
                    "frame": frame_data,
                    "person_count": 0,   # Placeholder until AI pipeline (Phase 16)
                    "crowd_state": "CALM",  # Placeholder
                    "alert": False         # Placeholder
                })

            payload = {
                "cameras": cameras_payload,
                "total_cameras": len(camera_manager.streams),
                "alert_active": False,
                "alert_camera": None,
                "target_track_id": None,
            }

            await websocket.send_json(payload)
            await asyncio.sleep(0.033)  # ~30 fps

    except WebSocketDisconnect:
        print(f"Client disconnected from /ws")
    except Exception as e:
        print(f"WebSocket error: {e}")

