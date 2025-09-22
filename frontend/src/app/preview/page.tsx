'use client'

import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import PreviewGenerator from '@/components/PreviewGenerator'

export default function PreviewPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <Link 
              href="/" 
              className="inline-flex items-center text-indigo-600 hover:text-indigo-700 mb-4"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Home
            </Link>
            <h1 className="text-3xl font-bold text-gray-900">Preview Generation</h1>
            <p className="text-gray-600 mt-2">
              Generate preview videos using the complete Persona Wizard pipeline
            </p>
          </div>

          {/* Preview Generator */}
          <PreviewGenerator />

          {/* Instructions */}
          <div className="mt-8 bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">How Preview Generation Works</h2>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Sample Data</h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Uses pre-generated sample text and voice</li>
                  <li>• Demonstrates the complete pipeline</li>
                  <li>• Shows lip-sync quality and performance</li>
                  <li>• No personal data required</li>
                </ul>
              </div>
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Custom Personas</h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Upload your own text, image, and voice</li>
                  <li>• Create personalized AI personas</li>
                  <li>• Generate custom preview videos</li>
                  <li>• Download complete persona bundles</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
