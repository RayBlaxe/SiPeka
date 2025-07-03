# Vehicle Detection and Counting System

This project implements a real-time vehicle detection and counting system using the YOLOv8 model. It can process video streams from a camera or a video file, identify vehicles (cars, motorcycles, buses, trucks), track them, and count them as they cross a predefined line.

## Features

- **Real-time vehicle detection:** Utilizes the YOLOv8 object detection model.
- **Vehicle tracking:** Assigns and tracks unique IDs for each detected vehicle.
- **Counting:** Counts vehicles crossing a designated line in either direction (in/out).
- **Input sources:** Supports both live camera feed and video files.
- **Output:** Displays the processed video with bounding boxes, tracking IDs, and counts. For video files, it saves the output as `output_counted.mp4`.
- **Customizable confidence threshold:** Allows adjustment of the detection confidence.
- **Reset functionality:** Option to reset counts during live camera processing.

## How it Works

The system performs the following steps:

1.  **Initialization:** Loads the YOLOv8 model and defines the vehicle classes to be detected.
2.  **Frame Processing:**
    *   Reads frames from the input source (camera or video).
    *   Runs the YOLOv8 model to detect objects in the frame.
    *   Filters detections to include only specified vehicle classes.
    *   Tracks detected vehicles using their assigned IDs and maintains a history of their positions.
    *   Draws bounding boxes and IDs on the vehicles.
3.  **Counting Logic:**
    *   A horizontal counting line is defined (defaulted to the middle of the frame).
    *   When a tracked vehicle's center crosses this line, it's counted as either 'in' or 'out' based on the direction of crossing.
    *   Each vehicle is counted only once.
4.  **Information Display:**
    *   Displays the total count, 'in' count, 'out' count, and current FPS on the video frame.
    *   For video file processing, it prints the progress to the console.

## Requirements

- Python 3.x
- OpenCV (`cv2`)
- NumPy
- Ultralytics YOLO (`ultralytics`)

Install the required libraries using pip:
```bash
pip install opencv-python numpy ultralytics
```

You will also need the YOLOv8 model weights file (e.g., `yolov8n.pt`). This is typically downloaded automatically by the `ultralytics` library the first time it's used, or you can provide a path to a local `.pt` file.

## Usage

The main script is `vehicle_detection.py`.

### Running with a Camera:

To use a live camera feed (e.g., webcam, typically source 0):

```bash
python vehicle_detection.py
```
The script defaults to `detector.run_camera(0)`.

During camera operation:
*   Press 'q' to quit the application.
*   Press 'r' to reset the vehicle counts.

### Running with a Video File:

To process a video file, modify the `if __name__ == "__main__":` block in `vehicle_detection.py`:

```python
if __name__ == "__main__":
    detector = VehicleDetectionSystem(confidence=0.5)
    # For video:
    detector.run_video('path/to/your/video.mp4') # Replace with your video file path
    # Example:
    # detector.run_video('sample_video.mp4')
```

Then run the script:
```bash
python vehicle_detection.py
```
The processed video will be saved as `output_counted.mp4` in the same directory.

## Files

- `vehicle_detection.py`: The main Python script containing the `VehicleDetectionSystem` class and execution logic.
- `yolov8n.pt` (example): YOLOv8 model weights file. This might be downloaded automatically or needs to be present.
- `sample_video.mp4` (example): An example video file that can be used for testing.
- `output_counted.mp4` (generated): The output video file when processing a local video.
- `README.md`: This file.
- `my_package/`: A sample package directory (currently not used by `vehicle_detection.py`).
- `my_package/subpackage/`: A sample subpackage directory (currently not used by `vehicle_detection.py`).

## Future Enhancements (Placeholder)
*   Configuration file for parameters (model path, confidence, line position).
*   Support for multiple counting lines.
*   More robust tracking algorithms.
*   Web interface for viewing results.
```
