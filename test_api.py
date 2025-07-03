#!/usr/bin/env python3
"""
Test script to check the /start endpoint
"""

import requests
import json

def test_start_endpoint():
    url = "http://localhost:8000/start"
    
    # Test data
    data = {
        "video_filename": "video_20250703_122435.mp4"
    }
    
    print(f"Testing /start endpoint with data: {data}")
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✓ Start endpoint working correctly")
        else:
            print(f"✗ Start endpoint failed with status {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error testing start endpoint: {e}")

def test_videos_endpoint():
    url = "http://localhost:8000/videos"
    
    print(f"Testing /videos endpoint")
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Videos found: {len(data['videos'])}")
        
        for video in data['videos']:
            print(f"  - {video['filename']} ({video['size_mb']} MB)")
            
    except Exception as e:
        print(f"✗ Error testing videos endpoint: {e}")

if __name__ == "__main__":
    print("Testing Vehicle Detection API Endpoints")
    print("=" * 50)
    
    test_videos_endpoint()
    print()
    test_start_endpoint()
