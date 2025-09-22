'use client'

import { useState, useEffect, useRef } from 'react'
import { Play, Pause, Loader2, RefreshCw, Download, Eye, Clock, FileText } from 'lucide-react'

interface Bundle {
  persona_id: string
  name: string
  description: string
  size_bytes: number
  created_at: string
}

interface InferenceResult {
  status: string
  persona_id: string
  prompt: string
  video_url: string
  duration: number
  fps: number
  size_px: number
  frame_count: number
  stdout: string
  stderr: string
}

interface InferenceProgress {
  status: 'idle' | 'running' | 'completed' | 'error'
  progress: number
  message: string
  result?: InferenceResult
  error?: string
}

export function BundleInference() {
  const [bundles, setBundles] = useState<Bundle[]>([])
  const [selectedBundle, setSelectedBundle] = useState<Bundle | null>(null)
  const [prompt, setPrompt] = useState('')
  const [inferenceProgress, setInferenceProgress] = useState<InferenceProgress>({
    status: 'idle',
    progress: 0,
    message: ''
  })
  const [playing, setPlaying] = useState(false)
  const [loading, setLoading] = useState(false)
  const [videoLoading, setVideoLoading] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)

  // Load bundles on mount
  useEffect(() => {
    loadBundles()
  }, [])

  const loadBundles = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8000/wizard/build/')
      
      if (!response.ok) {
        throw new Error('Failed to load bundles')
      }
      
      const data = await response.json()
      setBundles(data.bundles || [])
    } catch (error) {
      console.error('Failed to load bundles:', error)
    } finally {
      setLoading(false)
    }
  }

  const runInference = async () => {
    if (!selectedBundle || !prompt.trim()) return

    try {
      setInferenceProgress({
        status: 'running',
        progress: 0,
        message: 'Starting inference...'
      })

      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setInferenceProgress(prev => {
          if (prev.status !== 'running') return prev
          
          const newProgress = Math.min(prev.progress + Math.random() * 15, 90)
          let message = 'Processing...'
          
          if (newProgress < 20) message = 'Loading bundle...'
          else if (newProgress < 40) message = 'Generating text...'
          else if (newProgress < 60) message = 'Synthesizing voice...'
          else if (newProgress < 80) message = 'Generating lip-sync video...'
          else message = 'Finalizing output...'
          
          return { ...prev, progress: newProgress, message }
        })
      }, 500)

      const response = await fetch(`http://localhost:8000/wizard/build/${selectedBundle.persona_id}/inference`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: prompt.trim() })
      })

      clearInterval(progressInterval)

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Inference failed')
      }

      const result = await response.json()
      
      setInferenceProgress({
        status: 'completed',
        progress: 100,
        message: 'Inference completed!',
        result
      })

      // Auto-play the video when inference completes
      setVideoLoading(true)

    } catch (error) {
      setInferenceProgress({
        status: 'error',
        progress: 0,
        message: 'Inference failed',
        error: error instanceof Error ? error.message : 'Unknown error'
      })
    }
  }

  const togglePlay = () => {
    if (videoRef.current) {
      if (playing) {
        videoRef.current.pause()
      } else {
        videoRef.current.play()
      }
      setPlaying(!playing)
    }
  }

  const formatFileSize = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    if (bytes === 0) return '0 Bytes'
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const extractGeneratedText = (stdout: string) => {
    // Look for "Generated text:" in the stdout and extract the text that follows
    const generatedTextMatch = stdout.match(/Generated text:\s*(.+?)(?=\n\w+|\n$|$)/s)
    if (generatedTextMatch) {
      return generatedTextMatch[1].trim()
    }
    
    // Fallback: look for any text after "Generated text:" until the next major section
    const lines = stdout.split('\n')
    let inGeneratedText = false
    let generatedText = ''
    
    for (const line of lines) {
      if (line.includes('Generated text:')) {
        inGeneratedText = true
        const textStart = line.indexOf('Generated text:') + 'Generated text:'.length
        generatedText = line.substring(textStart).trim()
        continue
      }
      
      if (inGeneratedText) {
        // Stop when we hit the next major section
        if (line.includes('Synthesizing voice:') || 
            line.includes('Generating video:') || 
            line.includes('Error in') ||
            line.includes('Generated audio:') ||
            line.includes('Generated video:')) {
          break
        }
        
        if (line.trim()) {
          generatedText += '\n' + line.trim()
        }
      }
    }
    
    return generatedText.trim() || 'No generated text found in output.'
  }

  return (
    <div className="space-y-6">
      {/* Bundle Selection */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold mb-4">Select Persona Bundle</h3>
        
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin mr-2" />
            <span>Loading bundles...</span>
          </div>
        ) : bundles.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>No persona bundles found</p>
            <p className="text-sm">Create a persona first to see bundles here</p>
          </div>
        ) : (
          <div className="grid gap-3">
            {bundles.map((bundle) => (
              <div
                key={bundle.persona_id}
                className={`p-4 border rounded-lg cursor-pointer transition-all ${
                  selectedBundle?.persona_id === bundle.persona_id
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedBundle(bundle)}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-medium text-gray-900">{bundle.name}</h4>
                    <p className="text-sm text-gray-600">{bundle.description}</p>
                    <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                      <span className="flex items-center">
                        <Clock className="w-3 h-3 mr-1" />
                        {formatDate(bundle.created_at)}
                      </span>
                      <span>{formatFileSize(bundle.size_bytes)}</span>
                    </div>
                  </div>
                  {selectedBundle?.persona_id === bundle.persona_id && (
                    <div className="text-indigo-600">
                      <Eye className="w-5 h-5" />
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Inference Interface */}
      {selectedBundle && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Run Inference</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Prompt
              </label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Enter your prompt here... (e.g., 'Tell me about artificial intelligence')"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                rows={3}
                disabled={inferenceProgress.status === 'running'}
              />
            </div>

            <button
              onClick={runInference}
              disabled={!prompt.trim() || inferenceProgress.status === 'running'}
              className="w-full bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {inferenceProgress.status === 'running' ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Running Inference...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Run Inference
                </>
              )}
            </button>

            {/* Progress Bar */}
            {inferenceProgress.status === 'running' && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm text-gray-600">
                  <span>{inferenceProgress.message}</span>
                  <span>{Math.round(inferenceProgress.progress)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${
                      inferenceProgress.message?.includes('SadTalker')
                        ? 'bg-gradient-to-r from-blue-500 to-purple-600' // Special gradient for SadTalker
                        : 'bg-indigo-600'
                    }`}
                    style={{ width: `${inferenceProgress.progress}%` }}
                  />
                </div>
                {/* Show detailed stage for SadTalker */}
                {inferenceProgress.message?.includes('SadTalker') && (
                  <div className="text-xs text-gray-500 mt-1 bg-gray-50 p-2 rounded">
                    <div className="font-medium text-gray-700">SadTalker Progress:</div>
                    <div>{inferenceProgress.message.replace('SadTalker: ', '')}</div>
                  </div>
                )}
              </div>
            )}

            {/* Error Display */}
            {inferenceProgress.status === 'error' && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-md">
                <div className="flex items-center">
                  <div className="text-red-600 mr-2">⚠️</div>
                  <div>
                    <p className="text-red-800 font-medium">Inference Failed</p>
                    <p className="text-red-700 text-sm">{inferenceProgress.error}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Results Section - Side by Side Layout */}
      {inferenceProgress.status === 'completed' && inferenceProgress.result && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Generated Results</h3>
            {playing && (
              <div className="flex items-center text-green-600 text-sm">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2"></div>
                Auto-playing
              </div>
            )}
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Video Player - Left Side */}
            <div className="space-y-4">
              <h4 className="text-md font-medium text-gray-900 flex items-center">
                <Play className="w-4 h-4 mr-2" />
                Video Output
              </h4>
              
              <div className="relative bg-black rounded-lg overflow-hidden">
                <video
                  ref={videoRef}
                  src={`http://localhost:8000${inferenceProgress.result.video_url}`}
                  className="w-full h-64 object-cover"
                  onPlay={() => setPlaying(true)}
                  onPause={() => setPlaying(false)}
                  onEnded={() => setPlaying(false)}
                  onLoadStart={() => setVideoLoading(true)}
                  onCanPlay={() => {
                    setVideoLoading(false)
                    // Auto-play when video is ready
                    if (videoRef.current && inferenceProgress.status === 'completed') {
                      videoRef.current.play()
                      setPlaying(true)
                    }
                  }}
                  onError={() => setVideoLoading(false)}
                />
                
                {/* Video loading overlay */}
                {videoLoading && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-75">
                    <div className="text-center text-white">
                      <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2" />
                      <p className="text-sm">Loading video...</p>
                    </div>
                  </div>
                )}
                
                {/* Play/Pause overlay */}
                {!videoLoading && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <button
                      onClick={togglePlay}
                      className="bg-black bg-opacity-50 text-white rounded-full p-3 hover:bg-opacity-70 transition-all"
                    >
                      {playing ? (
                        <Pause className="w-6 h-6" />
                      ) : (
                        <Play className="w-6 h-6" />
                      )}
                    </button>
                  </div>
                )}
              </div>

              {/* Video Info */}
              <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="font-medium text-gray-900">{inferenceProgress.result.duration.toFixed(1)}s</div>
                    <div className="text-xs text-gray-500">Duration</div>
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">{inferenceProgress.result.size_px}px</div>
                    <div className="text-xs text-gray-500">Size</div>
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">{inferenceProgress.result.fps.toFixed(1)}</div>
                    <div className="text-xs text-gray-500">FPS</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Text Generation Output - Right Side */}
            <div className="space-y-4">
              <h4 className="text-md font-medium text-gray-900 flex items-center">
                <FileText className="w-4 h-4 mr-2" />
                Generated Text
              </h4>
              
              <div className="bg-gray-50 rounded-lg p-4 h-64 overflow-y-auto">
                <div className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
                  {extractGeneratedText(inferenceProgress.result.stdout)}
                </div>
              </div>
              
              {/* Text Stats */}
              <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
                <div className="flex justify-between items-center">
                  <span>Characters: {extractGeneratedText(inferenceProgress.result.stdout).length}</span>
                  <span>Words: {extractGeneratedText(inferenceProgress.result.stdout).split(/\s+/).length}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Regenerate Button */}
          <div className="text-center mt-6 pt-4 border-t border-gray-200">
            <button
              onClick={() => {
                setInferenceProgress({ status: 'idle', progress: 0, message: '' })
                setPrompt('')
                setVideoLoading(false)
                setPlaying(false)
              }}
              className="inline-flex items-center px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Generate New Video
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
