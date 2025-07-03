# backend.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import cv2
import numpy as np
from ultralytics import YOLO
from collections import defaultdict
import time
import json
import asyncio
from datetime import datetime
import threading
import base64

app = FastAPI()

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VehicleDetectionAPI:
    def __init__(self):
        self.model = YOLO('yolov8n.pt')
        self.confidence = 0.5
        self.vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck
        
        # Tracking
        self.track_history = defaultdict(lambda: [])
        self.vehicle_count = {'in': 0, 'out': 0, 'total': 0}
        self.counted_ids = set()
        self.counting_line = None
        
        # Report generation
        self.report_interval = 300  # 5 minutes in seconds
        self.last_report_time = time.time()
        self.reports = []
        
        # Video capture
        self.cap = None
        self.is_running = False
        
    def setup_counting_line(self, frame_height, position=0.5):
        self.counting_line = int(frame_height * position)
    
    def generate_report(self):
        """Generate periodic report"""
        current_time = datetime.now()
        report = {
            'timestamp': current_time.isoformat(),
            'duration_minutes': self.report_interval / 60,
            'vehicle_count': {
                'total': self.vehicle_count['total'],
                'incoming': self.vehicle_count['in'],
                'outgoing': self.vehicle_count['out']
            },
            'average_per_minute': {
                'total': self.vehicle_count['total'] / (self.report_interval / 60),
                'incoming': self.vehicle_count['in'] / (self.report_interval / 60),
                'outgoing': self.vehicle_count['out'] / (self.report_interval / 60)
            }
        }
        
        self.reports.append(report)
        
        # Save to file
        with open(f'report_{current_time.strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Reset counts for next period
        self.vehicle_count = {'in': 0, 'out': 0, 'total': 0}
        self.counted_ids.clear()
        self.last_report_time = time.time()
        
        return report
    
    def process_frame(self, frame):
        """Process single frame for detection and counting"""
        # Check if it's time for a report
        if time.time() - self.last_report_time >= self.report_interval:
            self.generate_report()
        
        # Run detection
        results = self.model.track(frame, persist=True, conf=self.confidence)
        
        # Initialize annotated frame
        annotated_frame = frame.copy()
        
        if results[0].boxes is not None and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.cpu().numpy().astype(int)
            classes = results[0].boxes.cls.cpu().numpy().astype(int)
            
            for box, track_id, cls in zip(boxes, track_ids, classes):
                if cls not in self.vehicle_classes:
                    continue
                
                x1, y1, x2, y2 = box.astype(int)
                center_y = int((y1 + y2) / 2)
                
                # Update tracking history
                self.track_history[track_id].append((int((x1 + x2) / 2), center_y))
                
                if len(self.track_history[track_id]) > 30:
                    self.track_history[track_id].pop(0)
                
                # Draw bounding box
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(annotated_frame, f'ID: {track_id}', (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # Check if vehicle crosses counting line
                if self.counting_line and track_id not in self.counted_ids:
                    if len(self.track_history[track_id]) > 10:
                        prev_y = self.track_history[track_id][-10][1]
                        curr_y = center_y
                        
                        if prev_y < self.counting_line < curr_y:
                            self.vehicle_count['in'] += 1
                            self.vehicle_count['total'] += 1
                            self.counted_ids.add(track_id)
                        elif prev_y > self.counting_line > curr_y:
                            self.vehicle_count['out'] += 1
                            self.vehicle_count['total'] += 1
                            self.counted_ids.add(track_id)
        
        # Draw counting line
        if self.counting_line:
            cv2.line(annotated_frame, (0, self.counting_line), 
                    (frame.shape[1], self.counting_line), (0, 0, 255), 2)
        
        return annotated_frame
    
    def get_frame_base64(self, frame):
        """Convert frame to base64 for web transmission"""
        _, buffer = cv2.imencode('.jpg', frame)
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        return frame_base64
    
    def start_capture(self, source=0):
        """Start video capture"""
        self.cap = cv2.VideoCapture(source)
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.setup_counting_line(frame.shape[0])
            self.is_running = True
            return True
        return False
    
    def stop_capture(self):
        """Stop video capture"""
        self.is_running = False
        if self.cap:
            self.cap.release()

# Initialize detector
detector = VehicleDetectionAPI()

@app.get("/")
async def root():
    return {"message": "Vehicle Detection API"}

@app.post("/start")
async def start_detection(source: int = 0):
    if detector.start_capture(source):
        return {"status": "started"}
    return {"status": "error", "message": "Failed to start capture"}

@app.post("/stop")
async def stop_detection():
    detector.stop_capture()
    return {"status": "stopped"}

@app.get("/stats")
async def get_stats():
    return {
        "counts": detector.vehicle_count,
        "is_running": detector.is_running,
        "reports": detector.reports[-5:]  # Last 5 reports
    }

@app.post("/set_report_interval")
async def set_report_interval(minutes: int):
    detector.report_interval = minutes * 60
    return {"status": "updated", "interval_minutes": minutes}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while detector.is_running:
            if detector.cap and detector.cap.isOpened():
                ret, frame = detector.cap.read()
                if ret:
                    # Process frame
                    processed_frame = detector.process_frame(frame)
                    
                    # Send frame and stats
                    frame_base64 = detector.get_frame_base64(processed_frame)
                    await websocket.send_json({
                        "frame": frame_base64,
                        "counts": detector.vehicle_count,
                        "timestamp": datetime.now().isoformat()
                    })
                    
            await asyncio.sleep(0.033)  # ~30 FPS
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@app.get("/download_reports")
async def download_reports():
    """Download all reports as JSON"""
    return {
        "reports": detector.reports,
        "summary": {
            "total_reports": len(detector.reports),
            "total_vehicles_all_time": sum(r['vehicle_count']['total'] for r in detector.reports)
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)