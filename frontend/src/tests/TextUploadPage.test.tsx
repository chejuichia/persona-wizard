import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import TextUploadPage from '@/app/wizard/text/page'

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

describe('TextUploadPage', () => {
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
    render(<TextUploadPage />)
    
    expect(screen.getByText('Upload Text for Style Analysis')).toBeInTheDocument()
    expect(screen.getByText('Upload Text')).toBeInTheDocument()
    expect(screen.getByText('Text Content')).toBeInTheDocument()
    expect(screen.getByText('Analyze Text')).toBeInTheDocument()
    expect(screen.getByText('Upload Text File')).toBeInTheDocument()
  })

  it('handles text input change', () => {
    render(<TextUploadPage />)
    
    const textarea = screen.getByPlaceholderText('Paste your text here... (minimum 10 characters)')
    fireEvent.change(textarea, { target: { value: 'This is a test text' } })
    
    expect(textarea).toHaveValue('This is a test text')
    expect(screen.getByText('19 characters')).toBeInTheDocument()
  })

  it('handles successful text upload', async () => {
    render(<TextUploadPage />)
    
    const textarea = screen.getByPlaceholderText('Paste your text here... (minimum 10 characters)')
    fireEvent.change(textarea, { target: { value: 'This is a comprehensive test text for style analysis.' } })
    
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        status: 'ok',
        text_id: 'test-text-id',
        session_id: 'test-session-id',
        token_count: 10,
        word_count: 8,
        character_count: 50,
        style_profile: {
          vocabulary_richness: 0.75,
          avg_sentence_length: 8.0,
          reading_ease: 65.5,
          tone: {
            positive: 0.3,
            negative: 0.1,
            formal: 0.6,
            casual: 0.4
          }
        },
        files: {
          raw_text: '/data/text/test_raw.txt',
          style_profile: '/data/text/test_profile.json'
        }
      })
    })

    const submitButton = screen.getByText('Analyze Text')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/wizard/text/upload',
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData)
        })
      )
    })

    await waitFor(() => {
      expect(screen.getByText('Analysis Complete')).toBeInTheDocument()
      expect(screen.getByText('8')).toBeInTheDocument() // word count
      expect(screen.getByText('50')).toBeInTheDocument() // character count
      expect(screen.getByText('10')).toBeInTheDocument() // token count
      expect(screen.getByText('65.5')).toBeInTheDocument() // reading ease
      expect(screen.getByText('75.0%')).toBeInTheDocument() // vocabulary richness
      expect(screen.getByText('8.0 words')).toBeInTheDocument() // avg sentence length
    })
  })

  it('handles text upload error', async () => {
    render(<TextUploadPage />)
    
    const textarea = screen.getByPlaceholderText('Paste your text here... (minimum 10 characters)')
    fireEvent.change(textarea, { target: { value: 'This is a test text' } })
    
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({
        detail: 'Text too short'
      })
    })

    const submitButton = screen.getByText('Analyze Text')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Text too short')).toBeInTheDocument()
    })
  })

  it('handles network error', async () => {
    render(<TextUploadPage />)
    
    const textarea = screen.getByPlaceholderText('Paste your text here... (minimum 10 characters)')
    fireEvent.change(textarea, { target: { value: 'This is a test text' } })
    
    ;(fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'))

    const submitButton = screen.getByText('Analyze Text')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument()
    })
  })

  it('handles file upload successfully', async () => {
    render(<TextUploadPage />)
    
    const file = new File(['This is test file content for analysis.'], 'test.txt', { type: 'text/plain' })
    
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        status: 'ok',
        text_id: 'test-file-id',
        session_id: 'test-session-id',
        token_count: 8,
        word_count: 7,
        character_count: 40,
        style_profile: {
          vocabulary_richness: 0.7,
          avg_sentence_length: 7.0,
          reading_ease: 70.0,
          tone: {
            positive: 0.2,
            negative: 0.1,
            formal: 0.5,
            casual: 0.5
          }
        },
        files: {
          raw_text: '/data/text/test_file_raw.txt',
          style_profile: '/data/text/test_file_profile.json'
        }
      })
    })

    const fileInput = screen.getByLabelText('Upload Text File')
    fireEvent.change(fileInput, { target: { files: [file] } })

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/wizard/text/upload-file',
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData)
        })
      )
    })

    await waitFor(() => {
      expect(screen.getByText('Analysis Complete')).toBeInTheDocument()
      expect(screen.getByText('7')).toBeInTheDocument() // word count
    })
  })

  it('handles file upload error', async () => {
    render(<TextUploadPage />)
    
    const file = new File(['test'], 'test.txt', { type: 'text/plain' })
    
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({
        detail: 'File too small'
      })
    })

    const fileInput = screen.getByLabelText('Upload Text File')
    fireEvent.change(fileInput, { target: { files: [file] } })

    await waitFor(() => {
      expect(screen.getByText('File too small')).toBeInTheDocument()
    })
  })

  it('disables submit button for empty text', () => {
    render(<TextUploadPage />)
    
    const submitButton = screen.getByText('Analyze Text')
    expect(submitButton).toBeDisabled()
  })

  it('disables submit button for whitespace-only text', () => {
    render(<TextUploadPage />)
    
    const textarea = screen.getByPlaceholderText('Paste your text here... (minimum 10 characters)')
    fireEvent.change(textarea, { target: { value: '   \n\t   ' } })
    
    const submitButton = screen.getByText('Analyze Text')
    expect(submitButton).toBeDisabled()
  })

  it('enables submit button for valid text', () => {
    render(<TextUploadPage />)
    
    const textarea = screen.getByPlaceholderText('Paste your text here... (minimum 10 characters)')
    fireEvent.change(textarea, { target: { value: 'This is valid text' } })
    
    const submitButton = screen.getByText('Analyze Text')
    expect(submitButton).not.toBeDisabled()
  })

  it('shows loading state during upload', async () => {
    render(<TextUploadPage />)
    
    const textarea = screen.getByPlaceholderText('Paste your text here... (minimum 10 characters)')
    fireEvent.change(textarea, { target: { value: 'This is a test text' } })
    
    // Mock a delayed response
    ;(fetch as jest.Mock).mockImplementationOnce(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({
            status: 'ok',
            text_id: 'test-text-id',
            session_id: 'test-session-id',
            token_count: 10,
            word_count: 8,
            character_count: 50,
            style_profile: {
              vocabulary_richness: 0.75,
              avg_sentence_length: 8.0,
              reading_ease: 65.5,
              tone: {
                positive: 0.3,
                negative: 0.1,
                formal: 0.6,
                casual: 0.4
              }
            },
            files: {
              raw_text: '/data/text/test_raw.txt',
              style_profile: '/data/text/test_profile.json'
            }
          })
        }), 100)
      )
    )

    const submitButton = screen.getByText('Analyze Text')
    fireEvent.click(submitButton)

    // Check loading state
    expect(screen.getByText('Analyzing...')).toBeInTheDocument()
  })

  it('disables buttons during upload', async () => {
    render(<TextUploadPage />)
    
    const textarea = screen.getByPlaceholderText('Paste your text here... (minimum 10 characters)')
    fireEvent.change(textarea, { target: { value: 'This is a test text' } })
    
    // Mock a delayed response
    ;(fetch as jest.Mock).mockImplementationOnce(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({
            status: 'ok',
            text_id: 'test-text-id',
            session_id: 'test-session-id',
            token_count: 10,
            word_count: 8,
            character_count: 50,
            style_profile: {
              vocabulary_richness: 0.75,
              avg_sentence_length: 8.0,
              reading_ease: 65.5,
              tone: {
                positive: 0.3,
                negative: 0.1,
                formal: 0.6,
                casual: 0.4
              }
            },
            files: {
              raw_text: '/data/text/test_raw.txt',
              style_profile: '/data/text/test_profile.json'
            }
          })
        }), 100)
      )
    )

    const submitButton = screen.getByText('Analyze Text')
    fireEvent.click(submitButton)

    // Check that buttons are disabled
    expect(screen.getByText('Analyzing...')).toBeDisabled()
    expect(screen.getByLabelText('Upload Text File')).toBeDisabled()
  })

  it('clears text area after file upload', async () => {
    render(<TextUploadPage />)
    
    const textarea = screen.getByPlaceholderText('Paste your text here... (minimum 10 characters)')
    fireEvent.change(textarea, { target: { value: 'Some text' } })
    
    const file = new File(['File content'], 'test.txt', { type: 'text/plain' })
    
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        status: 'ok',
        text_id: 'test-file-id',
        session_id: 'test-session-id',
        token_count: 2,
        word_count: 2,
        character_count: 12,
        style_profile: {
          vocabulary_richness: 0.5,
          avg_sentence_length: 2.0,
          reading_ease: 80.0,
          tone: {
            positive: 0.1,
            negative: 0.1,
            formal: 0.3,
            casual: 0.7
          }
        },
        files: {
          raw_text: '/data/text/test_file_raw.txt',
          style_profile: '/data/text/test_file_profile.json'
        }
      })
    })

    const fileInput = screen.getByLabelText('Upload Text File')
    fireEvent.change(fileInput, { target: { files: [file] } })

    await waitFor(() => {
      expect(textarea).toHaveValue('')
    })
  })

  it('navigates back when back button is clicked', () => {
    render(<TextUploadPage />)
    
    const backButton = screen.getByText('Back')
    fireEvent.click(backButton)
    
    expect(mockBack).toHaveBeenCalled()
  })

  it('navigates to image page when continue button is clicked', async () => {
    render(<TextUploadPage />)
    
    const textarea = screen.getByPlaceholderText('Paste your text here... (minimum 10 characters)')
    fireEvent.change(textarea, { target: { value: 'This is a comprehensive test text for style analysis.' } })
    
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        status: 'ok',
        text_id: 'test-text-id',
        session_id: 'test-session-id',
        token_count: 10,
        word_count: 8,
        character_count: 50,
        style_profile: {
          vocabulary_richness: 0.75,
          avg_sentence_length: 8.0,
          reading_ease: 65.5,
          tone: {
            positive: 0.3,
            negative: 0.1,
            formal: 0.6,
            casual: 0.4
          }
        },
        files: {
          raw_text: '/data/text/test_raw.txt',
          style_profile: '/data/text/test_profile.json'
        }
      })
    })

    const submitButton = screen.getByText('Analyze Text')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Continue to Image Upload')).toBeInTheDocument()
    })

    const continueButton = screen.getByText('Continue to Image Upload')
    fireEvent.click(continueButton)
    
    expect(mockPush).toHaveBeenCalledWith('/wizard/image')
  })

  it('shows character count correctly', () => {
    render(<TextUploadPage />)
    
    const textarea = screen.getByPlaceholderText('Paste your text here... (minimum 10 characters)')
    
    fireEvent.change(textarea, { target: { value: 'Hello' } })
    expect(screen.getByText('5 characters')).toBeInTheDocument()
    
    fireEvent.change(textarea, { target: { value: 'Hello World' } })
    expect(screen.getByText('11 characters')).toBeInTheDocument()
    
    fireEvent.change(textarea, { target: { value: '' } })
    expect(screen.getByText('0 characters')).toBeInTheDocument()
  })

  it('shows tone analysis correctly', async () => {
    render(<TextUploadPage />)
    
    const textarea = screen.getByPlaceholderText('Paste your text here... (minimum 10 characters)')
    fireEvent.change(textarea, { target: { value: 'This is a comprehensive test text for style analysis.' } })
    
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        status: 'ok',
        text_id: 'test-text-id',
        session_id: 'test-session-id',
        token_count: 10,
        word_count: 8,
        character_count: 50,
        style_profile: {
          vocabulary_richness: 0.75,
          avg_sentence_length: 8.0,
          reading_ease: 65.5,
          tone: {
            positive: 0.3,
            negative: 0.1,
            formal: 0.6,
            casual: 0.4
          }
        },
        files: {
          raw_text: '/data/text/test_raw.txt',
          style_profile: '/data/text/test_profile.json'
        }
      })
    })

    const submitButton = screen.getByText('Analyze Text')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('30.0%')).toBeInTheDocument() // positive tone
      expect(screen.getByText('60.0%')).toBeInTheDocument() // formal tone
    })
  })

  it('shows vocabulary richness progress bar', async () => {
    render(<TextUploadPage />)
    
    const textarea = screen.getByPlaceholderText('Paste your text here... (minimum 10 characters)')
    fireEvent.change(textarea, { target: { value: 'This is a comprehensive test text for style analysis.' } })
    
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        status: 'ok',
        text_id: 'test-text-id',
        session_id: 'test-session-id',
        token_count: 10,
        word_count: 8,
        character_count: 50,
        style_profile: {
          vocabulary_richness: 0.75,
          avg_sentence_length: 8.0,
          reading_ease: 65.5,
          tone: {
            positive: 0.3,
            negative: 0.1,
            formal: 0.6,
            casual: 0.4
          }
        },
        files: {
          raw_text: '/data/text/test_raw.txt',
          style_profile: '/data/text/test_profile.json'
        }
      })
    })

    const submitButton = screen.getByText('Analyze Text')
    fireEvent.click(submitButton)

    await waitFor(() => {
      const progressBar = screen.getByRole('progressbar', { hidden: true })
      expect(progressBar).toHaveStyle({ width: '75%' })
    })
  })

  it('handles form submission with enter key', async () => {
    render(<TextUploadPage />)
    
    const textarea = screen.getByPlaceholderText('Paste your text here... (minimum 10 characters)')
    fireEvent.change(textarea, { target: { value: 'This is a test text' } })
    
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        status: 'ok',
        text_id: 'test-text-id',
        session_id: 'test-session-id',
        token_count: 10,
        word_count: 8,
        character_count: 50,
        style_profile: {
          vocabulary_richness: 0.75,
          avg_sentence_length: 8.0,
          reading_ease: 65.5,
          tone: {
            positive: 0.3,
            negative: 0.1,
            formal: 0.6,
            casual: 0.4
          }
        },
        files: {
          raw_text: '/data/text/test_raw.txt',
          style_profile: '/data/text/test_profile.json'
        }
      })
    })

    fireEvent.submit(textarea.closest('form')!)

    await waitFor(() => {
      expect(fetch).toHaveBeenCalled()
    })
  })
})
