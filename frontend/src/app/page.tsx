import Link from 'next/link'
import { StatusPill } from '@/components/StatusPill'
import { BundleInference } from '@/components/BundleInference'

export default function HomePage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Persona Wizard
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Create AI personas with voice cloning and lip-sync video generation
          </p>
          <StatusPill />
        </div>

        {/* CTA - Moved to top */}
        <div className="text-center mb-12">
          <Link
            href="/wizard"
            className="inline-flex items-center px-8 py-4 border border-transparent text-lg font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all duration-200 transform hover:scale-105"
          >
            Start Creating Your Persona
          </Link>
          <p className="mt-4 text-sm text-gray-500">
            Click to begin the persona creation wizard
          </p>
        </div>

        {/* Features Grid - Smaller cards */}
        <div className="grid md:grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow-sm p-4">
            <div className="text-xl mb-2">🎤</div>
            <h3 className="text-base font-semibold mb-1">Voice Capture</h3>
            <p className="text-sm text-gray-600">
              Record 5-20 seconds of audio for voice cloning
            </p>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm p-4">
            <div className="text-xl mb-2">📝</div>
            <h3 className="text-base font-semibold mb-1">Text Style</h3>
            <p className="text-sm text-gray-600">
              Upload text to analyze and adapt writing style
            </p>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm p-4">
            <div className="text-xl mb-2">🖼️</div>
            <h3 className="text-base font-semibold mb-1">Portrait</h3>
            <p className="text-sm text-gray-600">
              Upload a portrait for face alignment and lip-sync
            </p>
          </div>
        </div>

        {/* Bundle Inference Section */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-2xl font-semibold mb-4">Try Your Personas</h2>
          <p className="text-gray-600 mb-6">
            Select from your created persona bundles and run local inference to see them in action. 
            Watch as your AI persona responds in your voice with lip-sync video generation.
          </p>
          <BundleInference />
        </div>

        {/* Disclaimer */}
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-6 mb-8">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <div className="text-amber-600 text-xl">⚠️</div>
            </div>
            <div className="ml-3">
              <h3 className="text-lg font-medium text-amber-800 mb-2">
                Demo Version - Not for Production Use
              </h3>
              <div className="text-sm text-amber-700 space-y-2">
                <p>
                  <strong>This is a demonstration version</strong> of Persona Wizard designed for research and experimentation purposes only. 
                  It is not intended for production use or commercial deployment.
                </p>
                <p>
                  <strong>Important Safety Notice:</strong> This application processes personal data including voice recordings, 
                  text samples, and images. Please ensure you have proper consent before using any data that belongs to others. 
                  Only use your own personal data or data you have explicit permission to use.
                </p>
                <p>
                  <strong>Responsible AI Development:</strong> We are actively working on implementing comprehensive guardrails, 
                  safety measures, and ethical guidelines to ensure responsible AI practices in local inference environments. 
                  Future versions will include enhanced privacy protections, content filtering, and usage monitoring.
                </p>
                <p className="text-xs text-amber-600 mt-3">
                  By using this application, you acknowledge that you understand these limitations and agree to use it responsibly.
                </p>
              </div>
            </div>
          </div>
        </div>


        {/* Footer */}
        <div className="mt-12 pt-8 border-t border-gray-200">
          <div className="text-center text-sm text-gray-500 space-y-2">
            <p>
              <strong>Persona Wizard</strong> - A demonstration of local AI persona creation technology
            </p>
            <p>
              Built with responsible AI principles in mind • Local inference • Privacy-focused
            </p>
            <p className="text-xs text-gray-400 mt-4">
              This tool is for educational and research purposes. Always respect privacy and consent when working with personal data.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
