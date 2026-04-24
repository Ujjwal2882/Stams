import { useState, useEffect } from "react";

export default function useWebSocket(url) {
  const [data, setData] = useState({
    cameras: [],
    total_cameras: 0,
    alert_active: false,
    alert_camera: null
  });

  useEffect(() => {
    let ws = null;
    let reconnectTimer = null;

    const connect = () => {
      console.log("Connecting to WebSocket...");
      ws = new WebSocket(url);

      ws.onopen = () => {
        console.log("WebSocket connected!");
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          setData(payload);
        } catch (e) {
          console.error("Error parsing WS data", e);
        }
      };

      ws.onclose = () => {
        console.log("WebSocket disconnected. Reconnecting in 2s...");
        reconnectTimer = setTimeout(connect, 2000);
      };

      ws.onerror = (err) => {
        console.error("WebSocket error", err);
        ws.close();
      };
    };

    connect();

    return () => {
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (ws) ws.close();
    };
  }, [url]);

  return data;
}
