# SentinelVision — Production Deployment Guide

This guide explains how to transition SentinelVision from a local development environment into a robust, high-performance production system.

## 1. Docker & Infrastructure Setup

### Remove Dev Overrides
In production, you should not mount local folders directly to the code (unless it's for persistent storage like `storage/` or `targets/`).
Update `docker-compose.yml` to remove the source code volume mounts, so the container uses the baked-in code.

### GPU Passthrough (Critical)
Ensure the host machine has the **NVIDIA Container Toolkit** installed. In your `docker-compose.yml`, uncomment the `runtime: nvidia` line:
```yaml
  backend:
    build: .
    ports:
      - "8000:8000"
    runtime: nvidia # MUST BE UNCOMMENTED
```

## 2. Model Optimization (TensorRT)

For a production pipeline running N cameras, PyTorch `fp32` models are too slow.
1. Make sure `USE_FP16=true` is set in `.env`.
2. Convert YOLOv8 to TensorRT for a massive latency reduction (Phase 23):
```bash
python scripts/export_tensorrt.py
```
This generates a `.engine` file that the system will automatically prefer over the `.pt` file.

## 3. Frontend Production Build

The `npm run dev` command starts a Vite development server, which is unoptimized. For production, you must build the static files and serve them using a robust web server (like Nginx).

### Option A: Update frontend/Dockerfile for Production
Use a multi-stage Docker build for the frontend:
```dockerfile
# Build Stage
FROM node:18-slim AS builder
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

# Serve Stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```
*Note: Update `docker-compose.yml` frontend port to `80:80` when using Nginx.*

## 4. Backend Production Server (Gunicorn)

Uvicorn is great, but in production, it should be managed by Gunicorn with Uvicorn workers to handle multiple concurrent connections and auto-restarts on crash.
Update the `CMD` in your backend `Dockerfile`:
```dockerfile
CMD ["gunicorn", "api.server:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```
*Note: Ensure `gunicorn` is added to `requirements.txt` before building.*

## 5. Reverse Proxy & Security (Nginx / Traefik)

Never expose ports `8000` or `5173` directly to the internet. 
1. Put an **Nginx** or **Traefik** reverse proxy in front of your containers.
2. Terminate SSL/TLS (HTTPS/WSS) at the reverse proxy. WebSockets (`ws://`) must be upgraded to secure WebSockets (`wss://`) in production to prevent browser security blocks.

## 6. Container Restart Policies

Add restart policies to your `docker-compose.yml` to ensure maximum uptime in case a container crashes:
```yaml
services:
  backend:
    restart: unless-stopped
    ...
```
