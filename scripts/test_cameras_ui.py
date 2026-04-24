import cv2
import time
from config import settings
from cameras.manager import CameraManager

def run_local_ui_test():
    print("--- SentinelVision Local UI Test ---")
    print(f"Configured camera sources: {settings.camera_sources_list}")
    
    manager = CameraManager()
    manager.start_all()
    
    try:
        print("\nOpening camera windows. Press 'q' on any window to exit.")
        while True:
            frames = manager.get_all_frames()
            
            if not frames:
                time.sleep(0.1)
                continue
                
            # Display each active camera in its own window
            for cam_id, frame in frames.items():
                window_name = f"Camera {cam_id}"
                
                # Resize frame for display so it fits nicely on screen if it's too big
                display_frame = cv2.resize(frame, (640, 480))
                
                # Add text to show it's active
                cv2.putText(display_frame, f"Cam {cam_id} Active", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                            
                cv2.imshow(window_name, display_frame)
                
            # Wait for 1 ms and check if 'q' was pressed to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Exit key pressed. Closing windows...")
                break
                
            time.sleep(0.03) # roughly 30 fps refresh
            
    except KeyboardInterrupt:
        print("\nInterrupted by user. Closing...")
    finally:
        manager.stop_all()
        cv2.destroyAllWindows()
        print("Done.")

if __name__ == "__main__":
    run_local_ui_test()
