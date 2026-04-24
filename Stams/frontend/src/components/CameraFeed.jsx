import React from "react";
import { motion } from "framer-motion";

function CameraFeed({ camera }) {
  const isAgitated = camera.crowd_state === "AGITATED";

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
      className={`relative rounded-xl overflow-hidden shadow-2xl border ${
        camera.alert
          ? "border-red-500 shadow-red-500/50"
          : "border-white/10 shadow-black/50"
      } bg-black/40 backdrop-blur-sm group`}
    >
      {/* Video Feed */}
      <img
        src={camera.frame}
        alt={`Camera ${camera.id}`}
        className="w-full h-full object-cover aspect-video"
      />

      {/* Overlay UI */}
      <div className="absolute top-0 left-0 w-full p-4 flex justify-between items-start bg-gradient-to-b from-black/80 to-transparent">
        <div className="flex items-center gap-3">
          <div className="bg-black/60 backdrop-blur-md px-3 py-1 rounded-md text-white font-mono text-sm border border-white/10 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
            CAM {camera.id.toString().padStart(2, "0")}
          </div>
        </div>

        <div className="flex flex-col gap-2 items-end">
          {/* Person Count Badge */}
          <div className="bg-black/60 backdrop-blur-md px-3 py-1 rounded-full text-white text-xs font-semibold border border-white/10 flex items-center gap-1 shadow-lg">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
            </svg>
            {camera.person_count} PERSONS
          </div>

          {/* Crowd State Badge */}
          <div
            className={`backdrop-blur-md px-3 py-1 rounded-full text-white text-xs font-bold border flex items-center shadow-lg transition-colors duration-300 ${
              isAgitated
                ? "bg-red-500/20 border-red-500/50 text-red-400"
                : "bg-green-500/20 border-green-500/50 text-green-400"
            }`}
          >
            {camera.crowd_state}
          </div>
        </div>
      </div>
      
      {/* Hover effect border */}
      <div className="absolute inset-0 border-2 border-transparent group-hover:border-blue-500/30 transition-colors duration-300 pointer-events-none rounded-xl"></div>
    </motion.div>
  );
}

export default CameraFeed;
