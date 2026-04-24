import React from "react";
import CameraFeed from "./CameraFeed";

function CameraGrid({ cameras, totalCameras }) {
  // Determine grid layout based on number of cameras
  let gridCols = "grid-cols-1";
  if (totalCameras >= 2 && totalCameras <= 4) gridCols = "grid-cols-2";
  else if (totalCameras >= 5 && totalCameras <= 9) gridCols = "grid-cols-3";
  else if (totalCameras >= 10) gridCols = "grid-cols-4";

  return (
    <div className={`grid gap-6 ${gridCols} auto-rows-fr`}>
      {cameras.map((cam) => (
        <CameraFeed key={cam.id} camera={cam} />
      ))}
    </div>
  );
}

export default CameraGrid;
