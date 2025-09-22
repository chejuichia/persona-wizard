'use client'

import { WizardProvider } from '@/contexts/WizardContext'

export default function WizardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <WizardProvider>
      {children}
    </WizardProvider>
  )
}
