
import cv2
import numpy as np
from ultralytics import YOLO
from collections import defaultdict
import time

class VehicleDetectionSystem:
    def __init__(self, model_path='yolov8n.pt', confidence=0.5):
        # Initialize YOLO model
        self.model = YOLO(model_path)
        self.confidence = confidence
        
        # Vehicle classes in COCO dataset
        self.vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck
        
        # Tracking
        self.track_history = defaultdict(lambda: [])
        self.vehicle_count = {'in': 0, 'out': 0, 'total': 0}
        self.counted_ids = set()
        
        # Counting line position (horizontal line at middle of frame)
        self.counting_line = None
        
    def setup_counting_line(self, frame_height, position=0.5):
        """Setup counting line position"""
        self.counting_line = int(frame_height * position)
        
    def process_frame(self, frame):
        """Process single frame for detection and counting"""
        # Run detection
        results = self.model.track(frame, persist=True, conf=self.confidence)
        
        # Initialize annotated frame
        annotated_frame = frame.copy()
        
        if results[0].boxes is not None and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.cpu().numpy().astype(int)
            classes = results[0].boxes.cls.cpu().numpy().astype(int)
            
            for box, track_id, cls in zip(boxes, track_ids, classes):
                # Filter only vehicle classes
                if cls not in self.vehicle_classes:
                    continue
                
                x1, y1, x2, y2 = box.astype(int)
                center_y = int((y1 + y2) / 2)
                
                # Update tracking history
                self.track_history[track_id].append((int((x1 + x2) / 2), center_y))
                
                # Keep only last 30 points
                if len(self.track_history[track_id]) > 30:
                    self.track_history[track_id].pop(0)
                
                # Draw bounding box
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(annotated_frame, f'ID: {track_id}', (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # Check if vehicle crosses counting line
                if self.counting_line and track_id not in self.counted_ids:
                    if len(self.track_history[track_id]) > 10:
                        # Get previous and current y positions
                        prev_y = self.track_history[track_id][-10][1]
                        curr_y = center_y
                        
                        # Check crossing
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
        
        # Display counts
        self._draw_info(annotated_frame)
        
        return annotated_frame
    
    def _draw_info(self, frame):
        """Draw counting information on frame"""
        # Background for text
        cv2.rectangle(frame, (10, 10), (300, 100), (0, 0, 0), -1)
        
        # Display counts
        cv2.putText(frame, f'Total: {self.vehicle_count["total"]}', (20, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f'In: {self.vehicle_count["in"]}', (20, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f'Out: {self.vehicle_count["out"]}', (150, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # FPS
        cv2.putText(frame, f'FPS: {self.fps:.1f}', (20, 85),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    def run_camera(self, source=0):
        """Run detection on camera feed"""
        cap = cv2.VideoCapture(source)
        
        if not cap.isOpened():
            raise ValueError("Cannot open camera")
        
        # Get frame dimensions
        ret, frame = cap.read()
        if ret:
            self.setup_counting_line(frame.shape[0])
        
        prev_time = time.time()
        self.fps = 0
        
        print("Press 'q' to quit, 'r' to reset counts")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Calculate FPS
            curr_time = time.time()
            self.fps = 1 / (curr_time - prev_time)
            prev_time = curr_time
            
            # Process frame
            processed_frame = self.process_frame(frame)
            
            # Display
            cv2.imshow('Vehicle Detection and Counting', processed_frame)
            
            # Handle key press
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                self.reset_counts()
        
        cap.release()
        cv2.destroyAllWindows()
    
    def run_video(self, video_path):
        """Run detection on video file"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        self.setup_counting_line(height)
        
        # Setup video writer for output
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter('output_counted.mp4', fourcc, fps, (width, height))
        
        frame_count = 0
        start_time = time.time()
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Calculate FPS
            elapsed = time.time() - start_time
            self.fps = frame_count / elapsed if elapsed > 0 else 0
            
            # Process frame
            processed_frame = self.process_frame(frame)
            
            # Write to output video
            out.write(processed_frame)
            
            # Display progress
            print(f"Processing frame {frame_count}, Vehicles: {self.vehicle_count['total']}", end='\r')
        
        print(f"\nProcessing complete! Total vehicles counted: {self.vehicle_count['total']}")
        
        cap.release()
        out.release()
        cv2.destroyAllWindows()
    
    def reset_counts(self):
        """Reset all counts and tracking"""
        self.vehicle_count = {'in': 0, 'out': 0, 'total': 0}
        self.counted_ids.clear()
        self.track_history.clear()
        print("Counts reset!")

# Main execution
if __name__ == "__main__":
    # Initialize system
    detector = VehicleDetectionSystem(confidence=0.5)
    
    # Choose input source
    # For camera: detector.run_camera(0)
    # For video: detector.run_video('path/to/video.mp4')
    
    # Run on default camera
    detector.run_camera(0)
    

