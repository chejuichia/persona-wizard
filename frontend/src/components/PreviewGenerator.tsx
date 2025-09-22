'use client'

import { useState, useEffect } from 'react'
import { Play, Pause, Square, Download, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react'

interface PreviewGeneratorProps {
  onPreviewGenerated?: (videoPath: string) => void
}

interface PreviewTask {
  task_id: string
  status: string
  progress: number
  current_step?: string
  message?: string
  video_path?: string
  audio_path?: string
  error?: string
}

export default function PreviewGenerator({ onPreviewGenerated }: PreviewGeneratorProps) {
  const [prompt, setPrompt] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [currentTask, setCurrentTask] = useState<PreviewTask | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [previewVideo, setPreviewVideo] = useState<string | null>(null)

  const generatePreview = async () => {
    if (!prompt.trim()) {
      setError('Please enter a prompt')
      return
    }

    setIsGenerating(true)
    setError(null)
    setCurrentTask(null)
    setPreviewVideo(null)

    try {
      const response = await fetch('/api/preview/generate-full', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: prompt.trim(),
          use_sample: true, // Use sample data for now
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to start preview generation')
      }

      const data = await response.json()
      setCurrentTask({
        task_id: data.task_id,
        status: data.status,
        progress: data.progress,
        message: data.message
      })

      // Start polling for status
      pollTaskStatus(data.task_id)
    } catch (err: any) {
      setError(err.message)
      setIsGenerating(false)
    }
  }

  const pollTaskStatus = async (taskId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/preview/status-full/${taskId}`)
        if (!response.ok) {
          throw new Error('Failed to get task status')
        }

        const task: PreviewTask = await response.json()
        setCurrentTask(task)

        if (task.status === 'completed') {
          setIsGenerating(false)
          clearInterval(pollInterval)
          
          if (task.video_path) {
            setPreviewVideo(task.video_path)
            onPreviewGenerated?.(task.video_path)
          }
        } else if (task.status === 'failed') {
          setIsGenerating(false)
          clearInterval(pollInterval)
          setError(task.error || 'Preview generation failed')
        }
      } catch (err: any) {
        setIsGenerating(false)
        clearInterval(pollInterval)
        setError(err.message)
      }
    }, 2000) // Poll every 2 seconds
  }

  const cancelGeneration = async () => {
    if (!currentTask) return

    try {
      await fetch(`/api/preview/tasks-full/${currentTask.task_id}`, {
        method: 'DELETE',
      })
      setIsGenerating(false)
      setCurrentTask(null)
    } catch (err: any) {
      setError(err.message)
    }
  }

  const downloadPreview = () => {
    if (previewVideo) {
      const link = document.createElement('a')
      link.href = previewVideo
      link.download = 'preview_video.mp4'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  }

  const getStatusIcon = () => {
    if (!currentTask) return null

    switch (currentTask.status) {
      case 'started':
      case 'generating_text':
      case 'generating_speech':
      case 'generating_video':
      case 'finalizing':
        return <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-600" />
      default:
        return null
    }
  }

  const getStatusMessage = () => {
    if (!currentTask) return 'Ready to generate preview'

    // If we have a detailed message from the backend, use it
    if (currentTask.message) {
      return currentTask.message
    }

    switch (currentTask.status) {
      case 'started':
        return 'Starting preview generation...'
      case 'generating_text':
        return 'Generating text with LLM...'
      case 'generating_speech':
        return 'Synthesizing speech with TTS...'
      case 'generating_video':
        return 'Generating video with SadTalker...'
      case 'finalizing':
        return 'Finalizing preview...'
      case 'completed':
        return 'Preview generated successfully!'
      case 'failed':
        return currentTask.error || 'Preview generation failed'
      default:
        return 'Processing...'
    }
  }

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Input Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Generate Preview</h2>
        
        <div className="space-y-4">
          <div>
            <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-2">
              Enter a prompt for your persona
            </label>
            <textarea
              id="prompt"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              rows={3}
              placeholder="e.g., 'Tell me about your favorite hobby' or 'Explain quantum computing in simple terms'"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              disabled={isGenerating}
            />
          </div>

          <div className="flex space-x-4">
            <button
              onClick={generatePreview}
              disabled={isGenerating || !prompt.trim()}
              className="flex items-center px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isGenerating ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Play className="w-4 h-4 mr-2" />
              )}
              {isGenerating ? 'Generating...' : 'Generate Preview'}
            </button>

            {isGenerating && (
              <button
                onClick={cancelGeneration}
                className="flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
              >
                <Square className="w-4 h-4 mr-2" />
                Cancel
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Status Section */}
      {currentTask && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">Generation Status</h3>
          
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              {getStatusIcon()}
              <span className="text-sm font-medium">{getStatusMessage()}</span>
            </div>

            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${
                  currentTask.status === 'generating_video' && currentTask.message?.includes('SadTalker')
                    ? 'bg-gradient-to-r from-blue-500 to-purple-600' // Special gradient for SadTalker
                    : 'bg-indigo-600'
                }`}
                style={{ width: `${currentTask.progress}%` }}
              />
            </div>

            <div className="text-sm text-gray-600">
              Progress: {currentTask.progress}%
            </div>

            {/* Show detailed stage for SadTalker */}
            {currentTask.status === 'generating_video' && currentTask.message?.includes('SadTalker') && (
              <div className="text-xs text-gray-500 mt-1 bg-gray-50 p-2 rounded">
                <div className="font-medium text-gray-700">SadTalker Progress:</div>
                <div>{currentTask.message.replace('SadTalker: ', '')}</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-400 mr-2" />
            <span className="text-sm text-red-800">{error}</span>
          </div>
        </div>
      )}

      {/* Preview Video */}
      {previewVideo && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Generated Preview</h3>
            <button
              onClick={downloadPreview}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
            >
              <Download className="w-4 h-4 mr-2" />
              Download
            </button>
          </div>

          <div className="bg-gray-100 rounded-lg p-4 text-center">
            <p className="text-gray-600 mb-4">
              Preview video generated successfully! The video shows your persona
              speaking the generated text with lip-sync animation.
            </p>
            
            <div className="bg-gray-200 rounded-lg p-8">
              <div className="text-gray-500">
                <Play className="w-12 h-12 mx-auto mb-2" />
                <p>Video Preview</p>
                <p className="text-sm">Click download to view the generated video</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 mb-2">How it works</h4>
        <div className="text-sm text-blue-800 space-y-1">
          <p>1. <strong>Text Generation:</strong> Your prompt is processed by an LLM to generate persona-appropriate text</p>
          <p>2. <strong>Voice Synthesis:</strong> The generated text is converted to speech using voice cloning</p>
          <p>3. <strong>Lip-Sync Video:</strong> SadTalker creates a talking head video with synchronized lip movement</p>
          <p>4. <strong>Preview Ready:</strong> Download the final MP4 video to see your persona in action</p>
        </div>
      </div>
    </div>
  )
}
