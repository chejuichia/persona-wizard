'use client'

import { useState, useEffect } from 'react'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'

interface HealthStatus {
  ok: boolean
  timestamp: string
  version: string
}

interface DeviceInfo {
  device: string
  cuda_available: boolean
  cuda_device_count: number
  memory_gb?: number
}

export function StatusPill() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [device, setDevice] = useState<DeviceInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const checkStatus = async () => {
      try {
        setLoading(true)
        setError(null)

        // Check health
        const healthResponse = await fetch('http://localhost:8000/healthz')
        if (!healthResponse.ok) {
          throw new Error(`Health check failed: ${healthResponse.status}`)
        }
        const healthData = await healthResponse.json()
        setHealth(healthData)

        // Check device info
        const deviceResponse = await fetch('http://localhost:8000/device')
        if (deviceResponse.ok) {
          const deviceData = await deviceResponse.json()
          setDevice(deviceData.device)
        }

      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    checkStatus()
    
    // Check status every 30 seconds
    const interval = setInterval(checkStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-yellow-100 text-yellow-800">
        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
        Checking status...
      </div>
    )
  }

  if (error) {
    return (
      <div className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-red-100 text-red-800">
        <XCircle className="w-4 h-4 mr-2" />
        Backend offline
      </div>
    )
  }

  if (health?.ok) {
    return (
      <div className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-green-100 text-green-800">
        <CheckCircle className="w-4 h-4 mr-2" />
        Backend online
        {device && (
          <span className="ml-2 text-xs">
            ({device.device} {device.cuda_available ? 'GPU' : 'CPU'})
          </span>
        )}
      </div>
    )
  }

  return (
    <div className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-red-100 text-red-800">
      <XCircle className="w-4 h-4 mr-2" />
      Backend error
    </div>
  )
}
