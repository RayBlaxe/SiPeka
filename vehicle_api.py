# backend.py
from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException
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
import os
import tempfile
import shutil
import logging

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        self.current_video_path = None
        self.video_info = None
        
        # Upload directory
        self.upload_dir = "uploads"
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
        
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
    
    def start_capture(self, video_path=None):
        """Start video capture from uploaded video file"""
        try:
            if not video_path:
                return False
                
            if not os.path.exists(video_path):
                logger.warning(f"Video file not found: {video_path}")
                return False
            
            self.cap = cv2.VideoCapture(video_path)
            if self.cap.isOpened():
                # Get video properties
                fps = self.cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                duration = frame_count / fps if fps > 0 else 0
                
                self.video_info = {
                    'fps': fps,
                    'frame_count': frame_count,
                    'width': width,
                    'height': height,
                    'duration': duration
                }
                
                # Test if we can actually read a frame
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    self.setup_counting_line(frame.shape[0])
                    self.is_running = True
                    self.current_video_path = video_path
                    # Reset video to beginning
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    logger.info(f"Successfully opened video: {video_path}")
                    logger.info(f"Video info: {self.video_info}")
                    return True
                else:
                    logger.warning(f"Video opened but can't read frames: {video_path}")
                    self.cap.release()
            else:
                logger.error(f"Failed to open video: {video_path}")
                
        except Exception as e:
            logger.error(f"Failed to start capture: {e}")
            if self.cap:
                self.cap.release()
                
        return False
    
    def upload_video(self, file: UploadFile):
        """Upload and save video file"""
        try:
            # Check file extension
            allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
            file_extension = os.path.splitext(file.filename)[1].lower()
            
            if file_extension not in allowed_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file format. Allowed: {', '.join(allowed_extensions)}"
                )
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"video_{timestamp}{file_extension}"
            file_path = os.path.join(self.upload_dir, filename)
            
            # Save uploaded file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Verify the video can be opened
            test_cap = cv2.VideoCapture(file_path)
            if not test_cap.isOpened():
                os.remove(file_path)  # Remove invalid file
                raise HTTPException(status_code=400, detail="Invalid video file")
            
            # Get video info
            fps = test_cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(test_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(test_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(test_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            
            video_info = {
                'filename': filename,
                'path': file_path,
                'fps': fps,
                'frame_count': frame_count,
                'width': width,
                'height': height,
                'duration': duration,
                'size_mb': os.path.getsize(file_path) / (1024 * 1024)
            }
            
            test_cap.release()
            
            logger.info(f"Video uploaded: {filename}, Size: {video_info['size_mb']} MB")
            
            return video_info
            
        except Exception as e:
            logger.error(f"Error uploading video: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def stop_capture(self):
        """Stop video capture"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        self.current_video_path = None
        self.video_info = None
    
    def get_uploaded_videos(self):
        """Get list of uploaded videos"""
        videos = []
        if os.path.exists(self.upload_dir):
            for filename in os.listdir(self.upload_dir):
                if filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm')):
                    file_path = os.path.join(self.upload_dir, filename)
                    file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                    videos.append({
                        'filename': filename,
                        'path': file_path,
                        'size_mb': round(file_size, 2),
                        'upload_time': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
                    })
        return videos
    
    def delete_video(self, filename):
        """Delete uploaded video"""
        file_path = os.path.join(self.upload_dir, filename)
        if os.path.exists(file_path):
            # Stop current video if it's the one being deleted
            if self.current_video_path == file_path:
                self.stop_capture()
            os.remove(file_path)
            logger.info(f"Video deleted: {filename}")
            return True
        return False

# Initialize detector
detector = VehicleDetectionAPI()

@app.get("/")
async def root():
    return {"message": "Vehicle Detection API - Video Upload Version"}

@app.post("/upload_video")
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file for processing"""
    video_info = detector.upload_video(file)
    return {"status": "uploaded", "video_info": video_info}

@app.get("/videos")
async def get_videos():
    """Get list of uploaded videos"""
    videos = detector.get_uploaded_videos()
    return {"videos": videos}

@app.delete("/videos/{filename}")
async def delete_video(filename: str):
    """Delete an uploaded video"""
    if detector.delete_video(filename):
        return {"status": "deleted", "filename": filename}
    else:
        raise HTTPException(status_code=404, detail="Video not found")

@app.post("/start")
async def start_detection(request: dict):
    """Start detection with uploaded video"""
    logger.info(f"Received start request: {request}")
    
    video_filename = request.get("video_filename")
    
    if not video_filename:
        logger.error("No video filename provided in request")
        return {
            "status": "error", 
            "message": "No video filename provided"
        }
    
    logger.info(f"Attempting to start detection with video: {video_filename}")
    
    video_path = os.path.join(detector.upload_dir, video_filename)
    logger.info(f"Video path: {video_path}")
    
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return {
            "status": "error", 
            "message": f"Video file not found: {video_filename}"
        }
    
    if detector.start_capture(video_path):
        logger.info(f"Successfully started detection for: {video_filename}")
        return {
            "status": "started", 
            "video_filename": video_filename,
            "video_info": detector.video_info
        }
    else:
        logger.error(f"Failed to start detection for: {video_filename}")
        available_videos = detector.get_uploaded_videos()
        return {
            "status": "error", 
            "message": f"Failed to start processing video: {video_filename}",
            "available_videos": available_videos
        }

@app.post("/stop")
async def stop_detection():
    detector.stop_capture()
    return {"status": "stopped"}

@app.get("/stats")
async def get_stats():
    return {
        "counts": detector.vehicle_count,
        "is_running": detector.is_running,
        "current_video": detector.current_video_path,
        "video_info": detector.video_info,
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
        while True:
            if detector.is_running and detector.cap and detector.cap.isOpened():
                ret, frame = detector.cap.read()
                if ret and frame is not None:
                    # Process frame
                    processed_frame = detector.process_frame(frame)
                    
                    # Send frame and stats
                    frame_base64 = detector.get_frame_base64(processed_frame)
                    await websocket.send_json({
                        "frame": frame_base64,
                        "counts": detector.vehicle_count,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    # Camera disconnected or error
                    await websocket.send_json({
                        "error": "Camera disconnected",
                        "counts": detector.vehicle_count,
                        "timestamp": datetime.now().isoformat()
                    })
                    break
            else:
                # No camera running, send status update
                await websocket.send_json({
                    "status": "waiting",
                    "counts": detector.vehicle_count,
                    "timestamp": datetime.now().isoformat()
                })
                    
            await asyncio.sleep(0.033)  # ~30 FPS
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({
            "error": str(e),
            "counts": detector.vehicle_count,
            "timestamp": datetime.now().isoformat()
        })
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