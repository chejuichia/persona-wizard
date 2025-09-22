'use client'

import { useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Upload, Image as ImageIcon, CheckCircle, AlertCircle, Eye, Loader2, History } from 'lucide-react'
import { Button } from '@/components/ui/button'
import ArtifactSelector from '@/components/ArtifactSelector'
import { useWizard } from '@/contexts/WizardContext'

interface ImageUploadResponse {
  status: string
  image_id: string
  session_id: string
  face_detected: boolean
  original_size: [number, number]
  output_size: [number, number]
  face_info?: {
    method: string
    confidence: number
    position: {
      x: number
      y: number
      width: number
      height: number
    }
  }
  files: {
    original: string
    face_ref: string
  }
}

interface ProcessingStep {
  id: string
  title: string
  description: string
  status: 'pending' | 'processing' | 'completed' | 'error'
}

interface Artifact {
  id: string;
  type: 'audio' | 'text' | 'image';
  name: string;
  created_at: string;
  file_path: string;
  metadata: any;
  size?: number;
  duration?: number;
  dimensions?: number[];
}

export default function ImageUploadPage() {
  const router = useRouter()
  const { setImageArtifact } = useWizard()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<ImageUploadResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [processingSteps, setProcessingSteps] = useState<ProcessingStep[]>([])
  const [currentStep, setCurrentStep] = useState<string | null>(null)
  const [selectedArtifact, setSelectedArtifact] = useState<Artifact | null>(null)
  const [showArtifactSelector, setShowArtifactSelector] = useState(false)

  const initializeProcessingSteps = () => {
    const steps: ProcessingStep[] = [
      {
        id: 'upload',
        title: 'Uploading Image',
        description: 'Sending your image to the server for processing...',
        status: 'pending'
      },
      {
        id: 'validation',
        title: 'Validating Image',
        description: 'Checking image format, size, and quality...',
        status: 'pending'
      },
      {
        id: 'face_detection',
        title: 'Detecting Face',
        description: 'Using AI to locate and analyze facial features...',
        status: 'pending'
      },
      {
        id: 'alignment',
        title: 'Aligning Face',
        description: 'Positioning and orienting the face for optimal results...',
        status: 'pending'
      },
      {
        id: 'preparation',
        title: 'Preparing for Lip-sync',
        description: 'Resizing and optimizing the image for video generation...',
        status: 'pending'
      },
      {
        id: 'finalization',
        title: 'Finalizing',
        description: 'Saving processed image and generating preview...',
        status: 'pending'
      }
    ]
    setProcessingSteps(steps)
    setCurrentStep('upload')
  }

  const updateStepStatus = (stepId: string, status: ProcessingStep['status']) => {
    setProcessingSteps(prev => 
      prev.map(step => 
        step.id === stepId 
          ? { ...step, status }
          : step
      )
    )
    if (status === 'processing') {
      setCurrentStep(stepId)
    }
  }

  const simulateProcessingProgress = async () => {
    // Simulate realistic processing times
    const delays = {
      upload: 500,
      validation: 800,
      face_detection: 1500,
      alignment: 1000,
      preparation: 800,
      finalization: 600
    }

    for (const [stepId, delay] of Object.entries(delays)) {
      updateStepStatus(stepId, 'processing')
      await new Promise(resolve => setTimeout(resolve, delay))
      updateStepStatus(stepId, 'completed')
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Create preview URL
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)
    
    // Upload the file
    uploadFile(file)
  }

  const uploadFile = async (file: File) => {
    setUploading(true)
    setError(null)
    initializeProcessingSteps()

    try {
      // Start progress simulation
      const progressPromise = simulateProcessingProgress()
      
      const formData = new FormData()
      formData.append('file', file)
      formData.append('session_id', 'frontend-upload')
      formData.append('target_size', '512')

      const response = await fetch('http://localhost:8000/wizard/image/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Upload failed')
      }

      const data = await response.json()
      
      // Wait for progress simulation to complete
      await progressPromise
      
      setResult(data)
      setPreviewUrl(`http://localhost:8000${data.files.face_ref}`)
      
      // Store image artifact in wizard context
      setImageArtifact(data.image_id, {
        face_detected: data.face_detected,
        original_size: data.original_size,
        output_size: data.output_size
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
      // Mark current step as error
      if (currentStep) {
        updateStepStatus(currentStep, 'error')
      }
    } finally {
      setUploading(false)
      setCurrentStep(null)
    }
  }

  const createSampleImage = async () => {
    setUploading(true)
    setError(null)
    initializeProcessingSteps()

    try {
      // Start progress simulation
      const progressPromise = simulateProcessingProgress()
      
      const formData = new FormData()
      formData.append('target_size', '512')

      const response = await fetch('http://localhost:8000/wizard/image/sample', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Sample creation failed')
      }

      const data = await response.json()
      
      // Wait for progress simulation to complete
      await progressPromise
      
      setResult(data)
      setPreviewUrl(`http://localhost:8000${data.files.face_ref}`)
      
      // Store image artifact in wizard context
      setImageArtifact(data.image_id, {
        face_detected: data.face_detected,
        original_size: data.original_size,
        output_size: data.output_size
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sample creation failed')
      // Mark current step as error
      if (currentStep) {
        updateStepStatus(currentStep, 'error')
      }
    } finally {
      setUploading(false)
      setCurrentStep(null)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const files = e.dataTransfer.files
    if (files.length > 0) {
      const file = files[0]
      if (file.type.startsWith('image/')) {
        handleFileSelect({ target: { files: [file] } } as any)
      } else {
        setError('Please select an image file')
      }
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const handleArtifactSelect = async (artifact: Artifact) => {
    setSelectedArtifact(artifact)
    setShowArtifactSelector(false)
    
    // Use the selected artifact for image processing
    try {
      setUploading(true)
      setError(null)
      initializeProcessingSteps()
      
      // Start progress simulation
      const progressPromise = simulateProcessingProgress()
      
      // Create a file from the artifact URL
      const response = await fetch(`http://localhost:8000/artifacts/${artifact.type}/${artifact.id}`)
      if (!response.ok) {
        throw new Error('Failed to fetch image file')
      }
      
      const blob = await response.blob()
      const file = new File([blob], artifact.name, { type: blob.type })
      
      // Process the image as if it were uploaded
      const formData = new FormData()
      formData.append('file', file)
      formData.append('session_id', 'frontend-upload')
      formData.append('target_size', '512')

      const uploadResponse = await fetch('http://localhost:8000/wizard/image/upload', {
        method: 'POST',
        body: formData,
      })

      if (!uploadResponse.ok) {
        const errorData = await uploadResponse.json()
        throw new Error(errorData.detail || 'Upload failed')
      }

      const data = await uploadResponse.json()
      
      // Wait for progress simulation to complete
      await progressPromise
      
      setResult(data)
      setPreviewUrl(`http://localhost:8000${data.files.face_ref}`)
      
      // Store image artifact in wizard context
      setImageArtifact(data.image_id, {
        face_detected: data.face_detected,
        original_size: data.original_size,
        output_size: data.output_size
      })
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to use selected artifact')
      // Mark current step as error
      if (currentStep) {
        updateStepStatus(currentStep, 'error')
      }
    } finally {
      setUploading(false)
      setCurrentStep(null)
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.back()}
            className="inline-flex items-center text-indigo-600 hover:text-indigo-700 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </button>
          <h1 className="text-3xl font-bold text-gray-900">
            Upload Portrait for Face Preparation
          </h1>
          <p className="text-gray-600 mt-2">
            Upload a portrait photo for face detection, alignment, and lip-sync preparation
          </p>
        </div>

        <div className="space-y-8">
          <div className="grid md:grid-cols-2 gap-8">
            {/* Upload Area */}
            <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Upload Image</h2>
              <Button
                onClick={() => setShowArtifactSelector(!showArtifactSelector)}
                variant="outline"
                size="sm"
                className="flex items-center space-x-2"
              >
                <History className="h-4 w-4" />
                <span>Use Previous</span>
              </Button>
            </div>
            
            {showArtifactSelector && (
              <div className="mb-6">
                <ArtifactSelector
                  onSelect={handleArtifactSelect}
                  selectedArtifact={selectedArtifact}
                  artifactType="image"
                  className="max-h-64 overflow-y-auto"
                />
              </div>
            )}
            
            <div
              className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-indigo-500 transition-colors"
              onDrop={handleDrop}
              onDragOver={handleDragOver}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileSelect}
                className="hidden"
                disabled={uploading}
              />
              
              <ImageIcon className="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <p className="text-lg font-medium text-gray-700 mb-2">
                Drop your image here or click to browse
              </p>
              <p className="text-sm text-gray-500 mb-4">
                Supported formats: JPG, PNG, BMP, TIFF, WebP (max 10MB)
              </p>
              
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploading ? 'Processing...' : 'Select Image'}
              </button>
            </div>

            <div className="mt-6">
              <div className="text-center">
                <p className="text-sm text-gray-500 mb-2">Or create a sample image for testing</p>
                <button
                  onClick={createSampleImage}
                  disabled={uploading}
                  className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {uploading ? 'Creating...' : 'Create Sample Image'}
                </button>
              </div>
            </div>

            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
                <div className="flex items-center">
                  <AlertCircle className="w-5 h-5 text-red-400 mr-2" />
                  <p className="text-red-800">{error}</p>
                </div>
              </div>
            )}
            </div>

            {/* Results */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">Processing Results</h2>
              
              {result ? (
                <div className="space-y-4">
                  <div className="flex items-center text-green-600">
                    <CheckCircle className="w-5 h-5 mr-2" />
                    <span className="font-medium">
                      {result.face_detected ? 'Face Detected' : 'No Face Detected'}
                    </span>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <p className="text-sm font-medium text-gray-700">Original Size</p>
                      <p className="text-lg">
                        {result.original_size[1]} × {result.original_size[0]} pixels
                      </p>
                    </div>

                    <div>
                      <p className="text-sm font-medium text-gray-700">Prepared Size</p>
                      <p className="text-lg">
                        {result.output_size[0]} × {result.output_size[1]} pixels
                      </p>
                    </div>

                    <div>
                      <p className="text-sm font-medium text-gray-700">Face Detection</p>
                      <p className={`text-lg ${result.face_detected ? 'text-green-600' : 'text-yellow-600'}`}>
                        {result.face_detected ? 'Success' : 'Used Center Crop'}
                      </p>
                      {result.face_info && (
                        <div className="mt-2 text-sm text-gray-600">
                          <p>Method: {result.face_info.method}</p>
                          <p>Confidence: {(result.face_info.confidence * 100).toFixed(1)}%</p>
                          <p>Position: ({result.face_info.position.x}, {result.face_info.position.y})</p>
                          <p>Size: {result.face_info.position.width} × {result.face_info.position.height}</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Preview */}
                  {previewUrl && (
                    <div className="mt-4">
                      <p className="text-sm font-medium text-gray-700 mb-2">Preview</p>
                      <div className="relative">
                        <img
                          src={previewUrl}
                          alt="Prepared face"
                          className="w-full h-48 object-cover rounded-lg border"
                        />
                        <div className="absolute top-2 right-2">
                          <a
                            href={previewUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="bg-black bg-opacity-50 text-white p-1 rounded hover:bg-opacity-70"
                          >
                            <Eye className="w-4 h-4" />
                          </a>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="pt-4 border-t">
                    <p className="text-sm text-gray-600 mb-2">Image ID: {result.image_id}</p>
                    <button
                      onClick={() => router.push('/wizard/build')}
                      className="w-full bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
                    >
                      Continue to Build Persona
                    </button>
                  </div>
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  <ImageIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>Upload an image to see processing results</p>
                </div>
              )}
            </div>
          </div>

          {/* Processing Progress */}
          {uploading && processingSteps.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">Processing Image</h2>
              
              <div className="space-y-4">
                {processingSteps.map((step, index) => (
                  <div key={step.id} className="flex items-start space-x-3">
                    <div className="flex-shrink-0 mt-1">
                      {step.status === 'completed' && (
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      )}
                      {step.status === 'processing' && (
                        <Loader2 className="w-5 h-5 text-indigo-500 animate-spin" />
                      )}
                      {step.status === 'error' && (
                        <AlertCircle className="w-5 h-5 text-red-500" />
                      )}
                      {step.status === 'pending' && (
                        <div className="w-5 h-5 rounded-full border-2 border-gray-300" />
                      )}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <h3 className={`text-sm font-medium ${
                          step.status === 'completed' ? 'text-green-700' :
                          step.status === 'processing' ? 'text-indigo-700' :
                          step.status === 'error' ? 'text-red-700' :
                          'text-gray-500'
                        }`}>
                          {step.title}
                        </h3>
                        {step.status === 'processing' && (
                          <span className="text-xs text-indigo-600 font-medium">
                            In Progress...
                          </span>
                        )}
                      </div>
                      <p className={`text-sm mt-1 ${
                        step.status === 'completed' ? 'text-green-600' :
                        step.status === 'processing' ? 'text-indigo-600' :
                        step.status === 'error' ? 'text-red-600' :
                        'text-gray-500'
                      }`}>
                        {step.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Overall Progress Bar */}
              <div className="mt-6">
                <div className="flex justify-between text-sm text-gray-600 mb-2">
                  <span>Overall Progress</span>
                  <span>
                    {processingSteps.filter(s => s.status === 'completed').length} / {processingSteps.length}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-indigo-600 h-2 rounded-full transition-all duration-300 ease-out"
                    style={{
                      width: `${(processingSteps.filter(s => s.status === 'completed').length / processingSteps.length) * 100}%`
                    }}
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
