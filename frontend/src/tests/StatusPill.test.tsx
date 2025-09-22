import { render, screen, waitFor } from '@testing-library/react'
import { StatusPill } from '@/components/StatusPill'
import { vi } from 'vitest'

// Mock fetch
global.fetch = vi.fn()

describe('StatusPill', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state initially', () => {
    render(<StatusPill />)
    expect(screen.getByText('Checking status...')).toBeInTheDocument()
  })

  it('shows error state when backend is offline', async () => {
    ;(fetch as vi.Mock).mockRejectedValue(new Error('Network error'))
    
    render(<StatusPill />)
    
    await waitFor(() => {
      expect(screen.getByText('Backend offline')).toBeInTheDocument()
    })
  })

  it('shows success state when backend is online', async () => {
    ;(fetch as vi.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ ok: true, timestamp: '2023-01-01T00:00:00Z', version: '0.1.0' })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ 
          device: { 
            device: 'cpu', 
            cuda_available: false, 
            cuda_device_count: 0 
          } 
        })
      })
    
    render(<StatusPill />)
    
    await waitFor(() => {
      expect(screen.getByText('Backend online')).toBeInTheDocument()
    })
  })
})
