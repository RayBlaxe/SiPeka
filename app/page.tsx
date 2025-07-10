// app/page.tsx
'use client'

import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Play, Square, Download, RefreshCw, Upload, Trash2, Video } from 'lucide-react'

interface VehicleStats {
  counts: {
    total: number
    in: number
    out: number
  }
  is_running: boolean
  current_video: string | null
  video_info: VideoInfo | null
  reports: Report[]
}

interface VideoInfo {
  fps: number
  frame_count: number
  width: number
  height: number
  duration: number
  filename?: string
  size_mb?: number
}

interface UploadedVideo {
  filename: string
  path: string
  size_mb: number
  upload_time: string
}

interface Report {
  timestamp: string
  duration_minutes: number
  vehicle_count: {
    total: number
    incoming: number
    outgoing: number
  }
  average_per_minute: {
    total: number
    incoming: number
    outgoing: number
  }
}

export default function VehicleDetection() {
  const [isRunning, setIsRunning] = useState(false)
  const [stats, setStats] = useState<VehicleStats>({
    counts: { total: 0, in: 0, out: 0 },
    is_running: false,
    current_video: null,
    video_info: null,
    reports: []
  })
  const [currentFrame, setCurrentFrame] = useState<string>('')
  const [reportInterval, setReportInterval] = useState(5)
  const [uploadedVideos, setUploadedVideos] = useState<UploadedVideo[]>([])
  const [selectedVideo, setSelectedVideo] = useState<string>('')
  const [isUploading, setIsUploading] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    fetchStats()
    fetchVideos()
    const interval = setInterval(fetchStats, 1000)
    return () => clearInterval(interval)
  }, [])

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/stats')
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    }
  }

  const fetchVideos = async () => {
    try {
      const response = await fetch('http://localhost:8000/videos')
      const data = await response.json()
      setUploadedVideos(data.videos)
    } catch (error) {
      console.error('Failed to fetch videos:', error)
    }
  }

  const uploadVideo = async (file: File) => {
    setIsUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch('http://localhost:8000/upload_video', {
        method: 'POST',
        body: formData
      })
      
      if (response.ok) {
        const data = await response.json()
        console.log('Video uploaded:', data)
        await fetchVideos() // Refresh video list
        setSelectedVideo(data.video_info.filename) // Auto-select uploaded video
      } else {
        const error = await response.json()
        console.error('Upload failed:', error)
        alert(`Upload failed: ${error.detail}`)
      }
    } catch (error) {
      console.error('Upload error:', error)
      alert('Upload failed. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      uploadVideo(file)
    }
  }

  const deleteVideo = async (filename: string) => {
    try {
      const response = await fetch(`http://localhost:8000/videos/${filename}`, {
        method: 'DELETE'
      })
      
      if (response.ok) {
        await fetchVideos()
        if (selectedVideo === filename) {
          setSelectedVideo('')
        }
      }
    } catch (error) {
      console.error('Failed to delete video:', error)
    }
  }

  const startDetection = async () => {
    if (!selectedVideo) {
      alert('Please select a video first')
      return
    }
    
    try {
      const response = await fetch('http://localhost:8000/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_filename: selectedVideo })
      })
      
      const data = await response.json()
      
      if (response.ok && data.status === 'started') {
        setIsRunning(true)
        connectWebSocket()
        console.log('Detection started successfully:', data)
      } else {
        console.error('Failed to start:', data)
        alert(`Failed to start: ${data.message || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Failed to start detection:', error)
      alert('Failed to start detection. Please try again.')
    }
  }

  const stopDetection = async () => {
    try {
      await fetch('http://localhost:8000/stop', { method: 'POST' })
      setIsRunning(false)
      if (wsRef.current) {
        wsRef.current.close()
      }
    } catch (error) {
      console.error('Failed to stop detection:', error)
    }
  }

  const connectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close()
    }
    
    const ws = new WebSocket('ws://localhost:8000/ws')
    
    ws.onopen = () => {
      console.log('WebSocket connected')
    }
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.frame) {
        setCurrentFrame(`data:image/jpeg;base64,${data.frame}`)
      }
      
      if (data.counts) {
        setStats(prev => ({ ...prev, counts: data.counts }))
      }
      
      if (data.error) {
        console.error('WebSocket error:', data.error)
        setIsRunning(false)
      }
      
      if (data.status === 'waiting') {
        console.log('Waiting for video processing...')
      }
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setIsRunning(false)
    }
    
    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setIsRunning(false)
    }
    
    wsRef.current = ws
  }

  const updateReportInterval = async () => {
    try {
      await fetch(`http://localhost:8000/set_report_interval?minutes=${reportInterval}`, {
        method: 'POST'
      })
    } catch (error) {
      console.error('Failed to update interval:', error)
    }
  }

  const downloadReports = async () => {
    try {
      const response = await fetch('http://localhost:8000/download_reports')
      const data = await response.json()
      
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: 'application/json'
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `vehicle_reports_${new Date().toISOString()}.json`
      a.click()
    } catch (error) {
      console.error('Failed to download reports:', error)
    }
  }

  return (
    <div className="container mx-auto p-4 max-w-6xl">
      <h1 className="text-3xl font-bold mb-6">SiPeka - Sistem Penghitung Kendaraan</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Video Processing</CardTitle>
          </CardHeader>
          <CardContent>
            {currentFrame ? (
              <div className="space-y-4">
                <img 
                  src={currentFrame} 
                  alt="Detection feed" 
                  className="w-full rounded-lg"
                />
                {stats.video_info && (
                  <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded">
                    <p><strong>Video:</strong> {stats.video_info.filename}</p>
                    <p><strong>Resolution:</strong> {stats.video_info.width}x{stats.video_info.height}</p>
                    <p><strong>FPS:</strong> {stats.video_info.fps.toFixed(1)}</p>
                    <p><strong>Duration:</strong> {Math.floor(stats.video_info.duration / 60)}:{(stats.video_info.duration % 60).toFixed(0).padStart(2, '0')}</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-gray-200 h-96 rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <Video className="mx-auto h-16 w-16 text-gray-400 mb-4" />
                  <p className="text-gray-500">No video selected</p>
                  <p className="text-sm text-gray-400">Upload and select a video to start detection</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
        
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Video Upload</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileSelect}
                accept="video/*"
                className="hidden"
              />
              <Button 
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="w-full"
                variant="outline"
              >
                {isUploading ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" /> Upload Video
                  </>
                )}
              </Button>
              
              {uploadedVideos.length > 0 && (
                <div className="space-y-2">
                  <label className="text-sm font-medium">Select Video:</label>
                  <select
                    value={selectedVideo}
                    onChange={(e) => setSelectedVideo(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    <option value="">Choose a video...</option>
                    {uploadedVideos.map((video) => (
                      <option key={video.filename} value={video.filename}>
                        {video.filename} ({video.size_mb.toFixed(1)} MB)
                      </option>
                    ))}
                  </select>
                </div>
              )}
              
              {selectedVideo && (
                <div className="flex gap-2">
                  <Button 
                    onClick={isRunning ? stopDetection : startDetection}
                    className="flex-1"
                    variant={isRunning ? "destructive" : "default"}
                  >
                    {isRunning ? (
                      <>
                        <Square className="mr-2 h-4 w-4" /> Stop
                      </>
                    ) : (
                      <>
                        <Play className="mr-2 h-4 w-4" /> Start
                      </>
                    )}
                  </Button>
                  <Button 
                    onClick={() => deleteVideo(selectedVideo)}
                    variant="outline"
                    size="sm"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex gap-2">
                <input
                  type="number"
                  value={reportInterval}
                  onChange={(e) => setReportInterval(Number(e.target.value))}
                  className="flex-1 px-3 py-2 border rounded-md"
                  min="1"
                  max="60"
                />
                <Button onClick={updateReportInterval} variant="outline">
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </div>
              <p className="text-sm text-gray-500">Report interval (minutes)</p>
              
              <Button onClick={downloadReports} variant="outline" className="w-full">
                <Download className="mr-2 h-4 w-4" /> Download Reports
              </Button>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Vehicle Count</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Total:</span>
                  <span className="font-bold text-xl">{stats.counts.total}</span>
                </div>
                <div className="flex justify-between text-green-600">
                  <span>Incoming:</span>
                  <span className="font-bold">{stats.counts.in}</span>
                </div>
                <div className="flex justify-between text-red-600">
                  <span>Outgoing:</span>
                  <span className="font-bold">{stats.counts.out}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
      
      {stats.reports.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Reports</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">Time</th>
                    <th className="text-right p-2">Total</th>
                    <th className="text-right p-2">In</th>
                    <th className="text-right p-2">Out</th>
                    <th className="text-right p-2">Avg/Min</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.reports.map((report, idx) => (
                    <tr key={idx} className="border-b">
                      <td className="p-2">
                        {new Date(report.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="text-right p-2">{report.vehicle_count.total}</td>
                      <td className="text-right p-2 text-green-600">
                        {report.vehicle_count.incoming}
                      </td>
                      <td className="text-right p-2 text-red-600">
                        {report.vehicle_count.outgoing}
                      </td>
                      <td className="text-right p-2">
                        {report.average_per_minute.total.toFixed(1)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}