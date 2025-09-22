'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Upload, FileText, CheckCircle, AlertCircle, History } from 'lucide-react'
import { Button } from '@/components/ui/button'
import ArtifactSelector from '@/components/ArtifactSelector'
import { useWizard } from '@/contexts/WizardContext'

interface TextUploadResponse {
  status: string
  text_id: string
  session_id: string
  token_count: number
  word_count: number
  character_count: number
  style_profile: {
    vocabulary_richness: number
    avg_sentence_length: number
    reading_ease: number
    tone: {
      positive: number
      negative: number
      formal: number
      casual: number
    }
  }
  files: {
    raw_text: string
    style_profile: string
  }
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

export default function TextUploadPage() {
  const router = useRouter()
  const { setTextArtifact } = useWizard()
  const [text, setText] = useState('')
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<TextUploadResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selectedArtifact, setSelectedArtifact] = useState<Artifact | null>(null)
  const [showArtifactSelector, setShowArtifactSelector] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!text.trim()) return

    setUploading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('text', text.trim())

      const response = await fetch('http://localhost:8000/wizard/text/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Upload failed')
      }

      const data = await response.json()
      setResult(data)
      // Store in wizard context
      setTextArtifact(data.text_id, {
        word_count: data.word_count,
        character_count: data.character_count,
        style_metrics: data.style_profile
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('http://localhost:8000/wizard/text/upload-file', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'File upload failed')
      }

      const data = await response.json()
      setResult(data)
      setText('') // Clear text area since we uploaded a file
    } catch (err) {
      setError(err instanceof Error ? err.message : 'File upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleArtifactSelect = async (artifact: Artifact) => {
    setSelectedArtifact(artifact)
    setShowArtifactSelector(false)
    
    // Use the selected artifact for text analysis
    try {
      setUploading(true)
      setError(null)
      
      // Fetch the text content from the artifact
      const response = await fetch(`http://localhost:8000/artifacts/${artifact.type}/${artifact.id}`)
      if (!response.ok) {
        throw new Error('Failed to fetch text file')
      }
      
      const textContent = await response.text()
      
      // Process the text as if it were manually entered
      setText(textContent)
      
      // Automatically submit for analysis
      const formData = new FormData()
      formData.append('text', textContent.trim())

      const analysisResponse = await fetch('http://localhost:8000/wizard/text/upload', {
        method: 'POST',
        body: formData,
      })

      if (!analysisResponse.ok) {
        const errorData = await analysisResponse.json()
        throw new Error(errorData.detail || 'Analysis failed')
      }

      const data = await analysisResponse.json()
      setResult(data)
      setTextArtifact(data.text_id, {
        word_count: data.word_count,
        character_count: data.character_count,
        style_metrics: data.style_profile
      })
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to use selected artifact')
    } finally {
      setUploading(false)
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
            Upload Text for Style Analysis
          </h1>
          <p className="text-gray-600 mt-2">
            Upload text samples to analyze your writing style and create a personalized AI persona
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Upload Form */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Upload Text</h2>
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
                  artifactType="text"
                  className="max-h-64 overflow-y-auto"
                />
              </div>
            )}
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="text" className="block text-sm font-medium text-gray-700 mb-2">
                  Text Content
                </label>
                <textarea
                  id="text"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  rows={12}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Paste your text here... (minimum 10 characters)"
                  disabled={uploading}
                />
                <p className="text-sm text-gray-500 mt-1">
                  {text.length} characters
                </p>
              </div>

              <div className="flex space-x-4">
                <button
                  type="submit"
                  disabled={!text.trim() || uploading}
                  className="flex-1 bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {uploading ? 'Analyzing...' : 'Analyze Text'}
                </button>
              </div>
            </form>

            <div className="mt-6">
              <div className="relative">
                <input
                  type="file"
                  id="file-upload"
                  accept=".txt,.md,.doc,.docx"
                  onChange={handleFileUpload}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  disabled={uploading}
                />
                <label
                  htmlFor="file-upload"
                  className="flex items-center justify-center w-full px-4 py-2 border-2 border-dashed border-gray-300 rounded-md cursor-pointer hover:border-indigo-500"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  Upload Text File
                </label>
              </div>
              <p className="text-sm text-gray-500 mt-2">
                Supported formats: .txt, .md, .doc, .docx (max 10MB)
              </p>
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
            <h2 className="text-xl font-semibold mb-4">Analysis Results</h2>
            
            {result ? (
              <div className="space-y-4">
                <div className="flex items-center text-green-600">
                  <CheckCircle className="w-5 h-5 mr-2" />
                  <span className="font-medium">Analysis Complete</span>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-50 p-3 rounded">
                    <p className="text-sm text-gray-600">Words</p>
                    <p className="text-lg font-semibold">{result.word_count.toLocaleString()}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded">
                    <p className="text-sm text-gray-600">Characters</p>
                    <p className="text-lg font-semibold">{result.character_count.toLocaleString()}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded">
                    <p className="text-sm text-gray-600">Tokens</p>
                    <p className="text-lg font-semibold">{result.token_count.toLocaleString()}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded">
                    <p className="text-sm text-gray-600">Reading Ease</p>
                    <p className="text-lg font-semibold">{result.style_profile.reading_ease.toFixed(1)}</p>
                  </div>
                </div>

                <div className="space-y-3">
                  <div>
                    <p className="text-sm font-medium text-gray-700">Vocabulary Richness</p>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-indigo-600 h-2 rounded-full"
                        style={{ width: `${result.style_profile.vocabulary_richness * 100}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {(result.style_profile.vocabulary_richness * 100).toFixed(1)}%
                    </p>
                  </div>

                  <div>
                    <p className="text-sm font-medium text-gray-700">Average Sentence Length</p>
                    <p className="text-lg">{result.style_profile.avg_sentence_length.toFixed(1)} words</p>
                  </div>

                  <div>
                    <p className="text-sm font-medium text-gray-700">Tone Analysis</p>
                    <div className="grid grid-cols-2 gap-2 mt-2">
                      <div className="text-center">
                        <p className="text-xs text-gray-600">Positive</p>
                        <p className="text-sm font-semibold">
                          {(result.style_profile.tone.positive * 100).toFixed(1)}%
                        </p>
                      </div>
                      <div className="text-center">
                        <p className="text-xs text-gray-600">Formal</p>
                        <p className="text-sm font-semibold">
                          {(result.style_profile.tone.formal * 100).toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t">
                  <p className="text-sm text-gray-600 mb-2">Text ID: {result.text_id}</p>
                  <button
                    onClick={() => router.push('/wizard/image')}
                    className="w-full bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
                  >
                    Continue to Image Upload
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>Upload text to see analysis results</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
