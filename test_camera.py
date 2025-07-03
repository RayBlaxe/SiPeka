#!/usr/bin/env python3
"""
Camera Test Script
Run this to diagnose camera issues
"""

import cv2
import numpy as np

def test_camera_access():
    """Test camera access with different backends"""
    
    print("Testing camera access...")
    print("=" * 50)
    
    # Test different backends
    backends = [
        (cv2.CAP_DSHOW, "DirectShow (Windows)"),
        (cv2.CAP_MSMF, "Media Foundation (Windows)"),
        (cv2.CAP_V4L2, "Video4Linux2 (Linux)"),
        (cv2.CAP_ANY, "Any available backend")
    ]
    
    available_cameras = []
    
    for camera_idx in range(5):  # Test cameras 0-4
        print(f"\nTesting Camera {camera_idx}:")
        print("-" * 30)
        
        camera_works = False
        
        for backend_id, backend_name in backends:
            try:
                cap = cv2.VideoCapture(camera_idx, backend_id)
                
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        height, width = frame.shape[:2]
                        print(f"  ✓ {backend_name}: Working ({width}x{height})")
                        camera_works = True
                        
                        # Test for a few frames
                        for i in range(3):
                            ret, frame = cap.read()
                            if not ret:
                                print(f"    ⚠ Frame {i+1} failed")
                                break
                        else:
                            print(f"    ✓ Successfully read 3 frames")
                    else:
                        print(f"  ✗ {backend_name}: Opens but no frames")
                else:
                    print(f"  ✗ {backend_name}: Cannot open")
                    
                cap.release()
                
            except Exception as e:
                print(f"  ✗ {backend_name}: Error - {e}")
        
        if camera_works:
            available_cameras.append(camera_idx)
    
    print(f"\n{'='*50}")
    print("SUMMARY:")
    print(f"Available cameras: {available_cameras}")
    
    if not available_cameras:
        print("\n⚠ No cameras detected!")
        print("Possible solutions:")
        print("1. Check if camera is connected")
        print("2. Close other applications using the camera")
        print("3. Check camera privacy settings")
        print("4. Try different USB ports")
        print("5. Update camera drivers")
    else:
        print(f"\n✓ Found {len(available_cameras)} working camera(s)")
        print("You can use these camera indices in your application")
    
    return available_cameras

def test_opencv_installation():
    """Test OpenCV installation"""
    print("\nTesting OpenCV installation...")
    print("=" * 50)
    
    try:
        print(f"OpenCV version: {cv2.__version__}")
        
        # Test video codecs
        fourcc_codes = ['XVID', 'MJPG', 'mp4v', 'H264']
        print("\nSupported video codecs:")
        for codec in fourcc_codes:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            print(f"  {codec}: {fourcc}")
        
        # Test camera backends
        print(f"\nCamera backends available:")
        backends = [
            'CAP_DSHOW', 'CAP_MSMF', 'CAP_V4L2', 'CAP_GSTREAMER', 
            'CAP_FFMPEG', 'CAP_OPENCV_MJPEG'
        ]
        
        for backend in backends:
            if hasattr(cv2, backend):
                print(f"  ✓ {backend}")
            else:
                print(f"  ✗ {backend}")
                
    except Exception as e:
        print(f"Error testing OpenCV: {e}")

def create_test_window():
    """Create a test window to verify display"""
    print("\nTesting display capabilities...")
    print("=" * 50)
    
    try:
        # Create a test image
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(img, "OpenCV Test", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
        
        cv2.imshow("Test Window", img)
        print("✓ Test window created")
        print("Press any key to close the test window...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        print("✓ Window closed successfully")
        
    except Exception as e:
        print(f"✗ Display test failed: {e}")

if __name__ == "__main__":
    print("Camera and OpenCV Diagnostic Tool")
    print("=" * 50)
    
    # Test OpenCV installation
    test_opencv_installation()
    
    # Test camera access
    available_cameras = test_camera_access()
    
    # Test display
    create_test_window()
    
    print(f"\n{'='*50}")
    print("FINAL RECOMMENDATIONS:")
    
    if available_cameras:
        print(f"✓ Use camera index: {available_cameras[0]} (recommended)")
        print("✓ Your system should work with the vehicle detection")
    else:
        print("✗ No cameras detected - fix camera issues first")
    
    print(f"{'='*50}")
