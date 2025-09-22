import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import ImageUploadPage from '@/app/wizard/image/page'

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      back: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
    }
  },
}))

// Mock fetch
global.fetch = jest.fn()

describe('ImageUploadPage', () => {
  const mockPush = jest.fn()
  const mockBack = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    ;(useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
      back: mockBack,
    })
    ;(fetch as jest.Mock).mockClear()
  })

  it('renders upload form correctly', () => {
    render(<ImageUploadPage />)
    
    expect(screen.getByText('Upload Portrait for Face Preparation')).toBeInTheDocument()
    expect(screen.getByText('Upload Image')).toBeInTheDocument()
    expect(screen.getByText('Drop your image here or click to browse')).toBeInTheDocument()
    expect(screen.getByText('Select Image')).toBeInTheDocument()
    expect(screen.getByText('Create Sample Image')).toBeInTheDocument()
  })

  it('handles file selection', async () => {
    render(<ImageUploadPage />)
    
    const file = new File(['test image content'], 'test.png', { type: 'image/png' })
    const fileInput = screen.getByRole('button', { name: /select image/i })
    
    // Mock successful upload response
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        status: 'ok',
        image_id: 'test-image-id',
        session_id: 'test-session-id',
        face_detected: true,
        original_size: [800, 600],
        output_size: [512, 512],
        files: {
          original: '/data/uploads/test.png',
          face_ref: '/data/portraits/test_face.png'
        }
      })
    })

    fireEvent.click(fileInput)
    
    // Simulate file selection
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/wizard/image/upload',
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData)
        })
      )
    })
  })

  it('handles successful image upload', async () => {
    render(<ImageUploadPage />)
    
    const file = new File(['test image content'], 'test.png', { type: 'image/png' })
    
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        status: 'ok',
        image_id: 'test-image-id',
        session_id: 'test-session-id',
        face_detected: true,
        original_size: [800, 600],
        output_size: [512, 512],
        files: {
          original: '/data/uploads/test.png',
          face_ref: '/data/portraits/test_face.png'
        }
      })
    })

    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => {
      expect(screen.getByText('Face Detected')).toBeInTheDocument()
      expect(screen.getByText('600 × 800 pixels')).toBeInTheDocument()
      expect(screen.getByText('512 × 512 pixels')).toBeInTheDocument()
      expect(screen.getByText('Success')).toBeInTheDocument()
      expect(screen.getByText('Continue to Build Persona')).toBeInTheDocument()
    })
  })

  it('handles image upload with no face detected', async () => {
    render(<ImageUploadPage />)
    
    const file = new File(['test image content'], 'test.png', { type: 'image/png' })
    
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        status: 'ok',
        image_id: 'test-image-id',
        session_id: 'test-session-id',
        face_detected: false,
        original_size: [800, 600],
        output_size: [512, 512],
        files: {
          original: '/data/uploads/test.png',
          face_ref: '/data/portraits/test_face.png'
        }
      })
    })

    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => {
      expect(screen.getByText('No Face Detected')).toBeInTheDocument()
      expect(screen.getByText('Used Center Crop')).toBeInTheDocument()
    })
  })

  it('handles upload error', async () => {
    render(<ImageUploadPage />)
    
    const file = new File(['test image content'], 'test.png', { type: 'image/png' })
    
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({
        detail: 'File too large'
      })
    })

    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => {
      expect(screen.getByText('File too large')).toBeInTheDocument()
    })
  })

  it('handles network error', async () => {
    render(<ImageUploadPage />)
    
    const file = new File(['test image content'], 'test.png', { type: 'image/png' })
    
    ;(fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'))

    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument()
    })
  })

  it('handles drag and drop', async () => {
    render(<ImageUploadPage />)
    
    const file = new File(['test image content'], 'test.png', { type: 'image/png' })
    const dropZone = screen.getByText('Drop your image here or click to browse').closest('div')
    
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        status: 'ok',
        image_id: 'test-image-id',
        session_id: 'test-session-id',
        face_detected: true,
        original_size: [800, 600],
        output_size: [512, 512],
        files: {
          original: '/data/uploads/test.png',
          face_ref: '/data/portraits/test_face.png'
        }
      })
    })

    fireEvent.drop(dropZone!, {
      dataTransfer: {
        files: [file]
      }
    })

    await waitFor(() => {
      expect(fetch).toHaveBeenCalled()
    })
  })

  it('handles drag and drop with invalid file type', async () => {
    render(<ImageUploadPage />)
    
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' })
    const dropZone = screen.getByText('Drop your image here or click to browse').closest('div')

    fireEvent.drop(dropZone!, {
      dataTransfer: {
        files: [file]
      }
    })

    await waitFor(() => {
      expect(screen.getByText('Please select an image file')).toBeInTheDocument()
    })
  })

  it('handles drag over event', () => {
    render(<ImageUploadPage />)
    
    const dropZone = screen.getByText('Drop your image here or click to browse').closest('div')
    
    fireEvent.dragOver(dropZone!)
    
    // Should not throw error
    expect(dropZone).toBeInTheDocument()
  })

  it('creates sample image successfully', async () => {
    render(<ImageUploadPage />)
    
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        status: 'ok',
        image_id: 'sample-image-id',
        session_id: 'sample-session-id',
        face_detected: true,
        original_size: [512, 512],
        output_size: [512, 512],
        files: {
          original: '/data/uploads/sample.png',
          face_ref: '/data/portraits/sample_face.png'
        }
      })
    })

    const sampleButton = screen.getByText('Create Sample Image')
    fireEvent.click(sampleButton)

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/wizard/image/sample',
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData)
        })
      )
    })

    await waitFor(() => {
      expect(screen.getByText('Face Detected')).toBeInTheDocument()
      expect(screen.getByText('512 × 512 pixels')).toBeInTheDocument()
    })
  })

  it('handles sample image creation error', async () => {
    render(<ImageUploadPage />)
    
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({
        detail: 'Sample creation failed'
      })
    })

    const sampleButton = screen.getByText('Create Sample Image')
    fireEvent.click(sampleButton)

    await waitFor(() => {
      expect(screen.getByText('Sample creation failed')).toBeInTheDocument()
    })
  })

  it('navigates back when back button is clicked', () => {
    render(<ImageUploadPage />)
    
    const backButton = screen.getByText('Back')
    fireEvent.click(backButton)
    
    expect(mockBack).toHaveBeenCalled()
  })

  it('navigates to build page when continue button is clicked', async () => {
    render(<ImageUploadPage />)
    
    const file = new File(['test image content'], 'test.png', { type: 'image/png' })
    
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        status: 'ok',
        image_id: 'test-image-id',
        session_id: 'test-session-id',
        face_detected: true,
        original_size: [800, 600],
        output_size: [512, 512],
        files: {
          original: '/data/uploads/test.png',
          face_ref: '/data/portraits/test_face.png'
        }
      })
    })

    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => {
      expect(screen.getByText('Continue to Build Persona')).toBeInTheDocument()
    })

    const continueButton = screen.getByText('Continue to Build Persona')
    fireEvent.click(continueButton)
    
    expect(mockPush).toHaveBeenCalledWith('/wizard/build')
  })

  it('shows loading state during upload', async () => {
    render(<ImageUploadPage />)
    
    const file = new File(['test image content'], 'test.png', { type: 'image/png' })
    
    // Mock a delayed response
    ;(fetch as jest.Mock).mockImplementationOnce(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({
            status: 'ok',
            image_id: 'test-image-id',
            session_id: 'test-session-id',
            face_detected: true,
            original_size: [800, 600],
            output_size: [512, 512],
            files: {
              original: '/data/uploads/test.png',
              face_ref: '/data/portraits/test_face.png'
            }
          })
        }), 100)
      )
    )

    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    fireEvent.change(input, { target: { files: [file] } })

    // Check loading state
    expect(screen.getByText('Processing...')).toBeInTheDocument()
    expect(screen.getByText('Creating...')).toBeInTheDocument()
  })

  it('disables buttons during upload', async () => {
    render(<ImageUploadPage />)
    
    const file = new File(['test image content'], 'test.png', { type: 'image/png' })
    
    // Mock a delayed response
    ;(fetch as jest.Mock).mockImplementationOnce(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({
            status: 'ok',
            image_id: 'test-image-id',
            session_id: 'test-session-id',
            face_detected: true,
            original_size: [800, 600],
            output_size: [512, 512],
            files: {
              original: '/data/uploads/test.png',
              face_ref: '/data/portraits/test_face.png'
            }
          })
        }), 100)
      )
    )

    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    fireEvent.change(input, { target: { files: [file] } })

    // Check that buttons are disabled
    const selectButton = screen.getByText('Processing...')
    const sampleButton = screen.getByText('Creating...')
    
    expect(selectButton).toBeDisabled()
    expect(sampleButton).toBeDisabled()
  })

  it('shows preview image when available', async () => {
    render(<ImageUploadPage />)
    
    const file = new File(['test image content'], 'test.png', { type: 'image/png' })
    
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        status: 'ok',
        image_id: 'test-image-id',
        session_id: 'test-session-id',
        face_detected: true,
        original_size: [800, 600],
        output_size: [512, 512],
        files: {
          original: '/data/uploads/test.png',
          face_ref: '/data/portraits/test_face.png'
        }
      })
    })

    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => {
      const previewImage = screen.getByAltText('Prepared face')
      expect(previewImage).toBeInTheDocument()
      expect(previewImage).toHaveAttribute('src', expect.stringContaining('blob:'))
    })
  })

  it('shows image info correctly', async () => {
    render(<ImageUploadPage />)
    
    const file = new File(['test image content'], 'test.png', { type: 'image/png' })
    
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        status: 'ok',
        image_id: 'test-image-id',
        session_id: 'test-session-id',
        face_detected: true,
        original_size: [800, 600],
        output_size: [512, 512],
        files: {
          original: '/data/uploads/test.png',
          face_ref: '/data/portraits/test_face.png'
        }
      })
    })

    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => {
      expect(screen.getByText('Image ID: test-image-id')).toBeInTheDocument()
      expect(screen.getByText('600 × 800 pixels')).toBeInTheDocument()
      expect(screen.getByText('512 × 512 pixels')).toBeInTheDocument()
    })
  })
})
