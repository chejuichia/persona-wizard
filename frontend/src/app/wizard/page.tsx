import Link from 'next/link'
import { ArrowLeft, ArrowRight } from 'lucide-react'

export default function WizardPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link 
            href="/"
            className="inline-flex items-center text-indigo-600 hover:text-indigo-700 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">
            Create Your Persona
          </h1>
          <p className="text-gray-600 mt-2">
            Follow the steps below to create your AI persona
          </p>
        </div>

        {/* Steps */}
        <div className="space-y-6">
          <Link href="/wizard/voice-capture" className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Step 1: Voice Capture
                </h3>
                <p className="text-gray-600">
                  Record 5-20 seconds of your voice for cloning
                </p>
              </div>
              <div className="text-sm text-indigo-600 font-medium">
                Ready
              </div>
            </div>
          </Link>

          <Link href="/wizard/text" className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Step 2: Text Upload
                </h3>
                <p className="text-gray-600">
                  Upload text samples to analyze your writing style
                </p>
              </div>
              <div className="text-sm text-indigo-600 font-medium">
                Ready
              </div>
            </div>
          </Link>

          <Link href="/wizard/image" className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Step 3: Image Upload
                </h3>
                <p className="text-gray-600">
                  Upload a portrait for face alignment
                </p>
              </div>
              <div className="text-sm text-indigo-600 font-medium">
                Ready
              </div>
            </div>
          </Link>

          <Link href="/wizard/build" className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Step 4: Build Persona
                </h3>
                <p className="text-gray-600">
                  Create a complete persona bundle with all artifacts
                </p>
              </div>
              <div className="text-sm text-indigo-600 font-medium">
                Ready
              </div>
            </div>
          </Link>

          <Link href="/preview" className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Step 5: Preview & Download
                </h3>
                <p className="text-gray-600">
                  Generate preview videos and download your persona
                </p>
              </div>
              <div className="text-sm text-indigo-600 font-medium">
                Ready
              </div>
            </div>
          </Link>
        </div>

        {/* Current Status */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-semibold text-blue-900 mb-2">
            Current Status: S5 - Full Preview Orchestration
          </h4>
          <p className="text-blue-800 text-sm">
            Complete preview generation pipeline is now working! You can generate preview videos 
            using the full LLM → TTS → SadTalker pipeline, build persona bundles with uploaded 
            samples, and download complete persona packages. All core functionality is ready!
          </p>
        </div>
      </div>
    </div>
  )
}
