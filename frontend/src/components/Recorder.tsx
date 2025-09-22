'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { Mic, MicOff, Square, Play, Pause } from 'lucide-react'

interface RecorderProps {
  onTranscription?: (text: string) => void
  onRecordingComplete?: (audioBlob: Blob) => void
  maxDuration?: number
  minDuration?: number
  sampleRate?: number
}

interface TranscriptionResult {
  type: 'partial' | 'final' | 'error'
  text: string
  confidence?: number
  language?: string
  wpm?: number
  duration?: number
  word_count?: number
}

export default function Recorder({
  onTranscription,
  onRecordingComplete,
  maxDuration = 20,
  minDuration = 5,
  sampleRate = 16000
}: RecorderProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [audioLevel, setAudioLevel] = useState(0)
  const [transcription, setTranscription] = useState('')
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const wsRef = useRef<WebSocket | null>(null)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animationFrameRef = useRef<number | null>(null)
  
  const sessionId = useRef<string>(Math.random().toString(36).substring(7))

  // Initialize WebSocket connection
  const connectWebSocket = useCallback(() => {
    // Temporarily disable WebSocket connection to fix voice recording
    console.log('WebSocket connection disabled - using fallback transcription')
    setIsConnected(false)
    setError('Real-time transcription temporarily disabled - recording will still work')
  }, [onTranscription])

  // Start recording
  const startRecording = useCallback(async () => {
    try {
      setError(null)
      setTranscription('')
      audioChunksRef.current = []
      
      // Connect WebSocket
      connectWebSocket()
      
      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: sampleRate,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      })
      
      // Set up audio analysis for level monitoring
      const audioContext = new AudioContext({ sampleRate })
      const analyser = audioContext.createAnalyser()
      const source = audioContext.createMediaStreamSource(stream)
      source.connect(analyser)
      
      analyser.fftSize = 256
      analyser.smoothingTimeConstant = 0.8
      
      audioContextRef.current = audioContext
      analyserRef.current = analyser
      
      // Start audio level monitoring
      const monitorAudioLevel = () => {
        if (!analyser) return
        
        const dataArray = new Uint8Array(analyser.frequencyBinCount)
        analyser.getByteFrequencyData(dataArray)
        
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length
        setAudioLevel(average / 255)
        
        animationFrameRef.current = requestAnimationFrame(monitorAudioLevel)
      }
      monitorAudioLevel()
      
      // Set up MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
          
          // Send audio data to WebSocket
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            event.data.arrayBuffer().then(buffer => {
              wsRef.current?.send(buffer)
            })
          }
        }
      }
      
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        onRecordingComplete?.(audioBlob)
        
        // Clean up audio context
        if (audioContextRef.current) {
          audioContextRef.current.close()
          audioContextRef.current = null
        }
        
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current)
          animationFrameRef.current = null
        }
      }
      
      mediaRecorderRef.current = mediaRecorder
      mediaRecorder.start(100) // Send data every 100ms
      
      setIsRecording(true)
      setIsPaused(false)
      setRecordingTime(0)
      
      // Start timer
      intervalRef.current = setInterval(() => {
        setRecordingTime(prev => {
          const newTime = prev + 0.1
          if (newTime >= maxDuration) {
            stopRecording()
            return maxDuration
          }
          return newTime
        })
      }, 100)
      
    } catch (err) {
      console.error('Failed to start recording:', err)
      setError('Failed to start recording. Please check microphone permissions.')
    }
  }, [connectWebSocket, onRecordingComplete, maxDuration, sampleRate])

  // Stop recording
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      setIsPaused(false)
      
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      
      // Close WebSocket
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [isRecording])

  // Pause/Resume recording
  const togglePause = useCallback(() => {
    if (!mediaRecorderRef.current) return
    
    if (isPaused) {
      mediaRecorderRef.current.resume()
      setIsPaused(false)
    } else {
      mediaRecorderRef.current.pause()
      setIsPaused(true)
    }
  }, [isPaused])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    }
  }, [])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const getRecordingStatus = () => {
    if (isRecording && isPaused) return 'Paused'
    if (isRecording) return 'Recording'
    return 'Ready'
  }

  const canStop = isRecording && recordingTime >= minDuration
  const isNearMax = recordingTime >= maxDuration * 0.9

  return (
    <div className="w-full max-w-md mx-auto">
      {/* Status */}
      <div className="text-center mb-4">
        <div className={`text-sm font-medium ${
          isConnected ? 'text-green-600' : 'text-red-600'
        }`}>
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
        <div className="text-lg font-semibold text-gray-900">
          {getRecordingStatus()}
        </div>
        <div className="text-2xl font-mono text-gray-600">
          {formatTime(recordingTime)}
        </div>
      </div>

      {/* Audio Level Indicator */}
      {isRecording && (
        <div className="mb-4">
          <div className="text-sm text-gray-600 mb-2">Audio Level</div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-indigo-600 h-2 rounded-full transition-all duration-100"
              style={{ width: `${audioLevel * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="flex justify-center space-x-4 mb-4">
        {!isRecording ? (
          <button
            onClick={startRecording}
            className="flex items-center px-6 py-3 bg-red-600 text-white rounded-full hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
          >
            <Mic className="w-5 h-5 mr-2" />
            Start Recording
          </button>
        ) : (
          <>
            <button
              onClick={togglePause}
              className="flex items-center px-4 py-3 bg-yellow-600 text-white rounded-full hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2"
            >
              {isPaused ? (
                <Play className="w-5 h-5" />
              ) : (
                <Pause className="w-5 h-5" />
              )}
            </button>
            
            <button
              onClick={stopRecording}
              disabled={!canStop}
              className={`flex items-center px-6 py-3 rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                canStop
                  ? 'bg-gray-600 text-white hover:bg-gray-700 focus:ring-gray-500'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              <Square className="w-5 h-5 mr-2" />
              Stop Recording
            </button>
          </>
        )}
      </div>

      {/* Duration Warning */}
      {isRecording && (
        <div className={`text-center text-sm ${
          isNearMax ? 'text-red-600' : 'text-gray-600'
        }`}>
          {isNearMax ? 'Maximum duration reached' : `Minimum: ${minDuration}s, Maximum: ${maxDuration}s`}
        </div>
      )}

      {/* Transcription */}
      {transcription && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <div className="text-sm font-medium text-gray-700 mb-2">Live Transcription:</div>
          <div className="text-gray-900">{transcription}</div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="text-sm text-red-800">{error}</div>
        </div>
      )}

      {/* Instructions */}
      <div className="mt-6 text-sm text-gray-600">
        <p className="mb-2">Recording Tips:</p>
        <ul className="list-disc list-inside space-y-1">
          <li>Speak clearly and at normal volume</li>
          <li>Record for 5-20 seconds for best results</li>
          <li>Ensure you're in a quiet environment</li>
          <li>Hold the microphone 6-12 inches from your mouth</li>
        </ul>
      </div>
    </div>
  )
}
