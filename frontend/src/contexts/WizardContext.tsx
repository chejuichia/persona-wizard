'use client'

import React, { createContext, useContext, useState, ReactNode } from 'react'

interface UploadedArtifacts {
  textId?: string
  imageId?: string
  voiceId?: string
  textMetadata?: {
    word_count: number
    character_count: number
    style_metrics: any
  }
  imageMetadata?: {
    face_detected: boolean
    original_size: [number, number]
    output_size: [number, number]
  }
  voiceMetadata?: {
    duration: number
    sample_rate: number
    reference_text: string
  }
}

interface WizardContextType {
  artifacts: UploadedArtifacts
  setTextArtifact: (textId: string, metadata: any) => void
  setImageArtifact: (imageId: string, metadata: any) => void
  setVoiceArtifact: (voiceId: string, metadata: any) => void
  clearArtifacts: () => void
  hasArtifacts: () => boolean
}

const WizardContext = createContext<WizardContextType | undefined>(undefined)

export function WizardProvider({ children }: { children: ReactNode }) {
  const [artifacts, setArtifacts] = useState<UploadedArtifacts>({})

  const setTextArtifact = (textId: string, metadata: any) => {
    setArtifacts(prev => ({
      ...prev,
      textId,
      textMetadata: metadata
    }))
  }

  const setImageArtifact = (imageId: string, metadata: any) => {
    setArtifacts(prev => ({
      ...prev,
      imageId,
      imageMetadata: metadata
    }))
  }

  const setVoiceArtifact = (voiceId: string, metadata: any) => {
    setArtifacts(prev => ({
      ...prev,
      voiceId,
      voiceMetadata: metadata
    }))
  }

  const clearArtifacts = () => {
    setArtifacts({})
  }

  const hasArtifacts = () => {
    return !!(artifacts.textId || artifacts.imageId || artifacts.voiceId)
  }

  return (
    <WizardContext.Provider value={{
      artifacts,
      setTextArtifact,
      setImageArtifact,
      setVoiceArtifact,
      clearArtifacts,
      hasArtifacts
    }}>
      {children}
    </WizardContext.Provider>
  )
}

export function useWizard() {
  const context = useContext(WizardContext)
  if (context === undefined) {
    throw new Error('useWizard must be used within a WizardProvider')
  }
  return context
}
