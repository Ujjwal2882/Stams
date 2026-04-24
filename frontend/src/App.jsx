import React from "react";
import CameraGrid from "./components/CameraGrid";
import useWebSocket from "./hooks/useWebSocket";

function App() {
  const wsUrl = "ws://localhost:8000/ws";
  const data = useWebSocket(wsUrl);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-[#111827] to-black text-white p-6 font-sans">
      <header className="mb-8 border-b border-white/10 pb-4 flex justify-between items-center backdrop-blur-md">
        <div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
            SentinelVision
          </h1>
          <p className="text-gray-400 text-sm mt-1 tracking-wide">
            REAL-TIME MULTI-CAMERA AI SURVEILLANCE
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-white/5 px-4 py-2 rounded-full border border-white/10">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
            </span>
            <span className="text-sm font-medium text-gray-300">
              {data.total_cameras} {data.total_cameras === 1 ? 'Camera' : 'Cameras'} Active
            </span>
          </div>
        </div>
      </header>

      <main>
        {data.cameras.length > 0 ? (
          <CameraGrid cameras={data.cameras} totalCameras={data.total_cameras} />
        ) : (
          <div className="flex flex-col items-center justify-center h-[60vh] border border-dashed border-white/20 rounded-2xl bg-white/5 backdrop-blur-sm">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
            <p className="text-gray-400 text-lg">Waiting for camera feeds...</p>
            <p className="text-gray-500 text-sm mt-2">Ensure the Python backend is running.</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
