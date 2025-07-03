// app/page.tsx
'use client'

import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Play, Square, Download, RefreshCw } from 'lucide-react'

interface VehicleStats {
  counts: {
    total: number
    in: number
    out: number
  }
  is_running: boolean
  reports: Report[]
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
    reports: []
  })
  const [currentFrame, setCurrentFrame] = useState<string>('')
  const [reportInterval, setReportInterval] = useState(5)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    fetchStats()
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

  const startDetection = async () => {
    try {
      const response = await fetch('http://localhost:8000/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: 0 })
      })
      
      if (response.ok) {
        setIsRunning(true)
        connectWebSocket()
      }
    } catch (error) {
      console.error('Failed to start detection:', error)
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
    const ws = new WebSocket('ws://localhost:8000/ws')
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setCurrentFrame(`data:image/jpeg;base64,${data.frame}`)
      setStats(prev => ({ ...prev, counts: data.counts }))
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
    
    ws.onclose = () => {
      console.log('WebSocket disconnected')
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
      <h1 className="text-3xl font-bold mb-6">Vehicle Detection System</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Live Feed</CardTitle>
          </CardHeader>
          <CardContent>
            {currentFrame ? (
              <img 
                src={currentFrame} 
                alt="Detection feed" 
                className="w-full rounded-lg"
              />
            ) : (
              <div className="bg-gray-200 h-96 rounded-lg flex items-center justify-center">
                <p className="text-gray-500">No feed available</p>
              </div>
            )}
          </CardContent>
        </Card>
        
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Controls</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button 
                onClick={isRunning ? stopDetection : startDetection}
                className="w-full"
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
              <CardTitle>Current Count</CardTitle>
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