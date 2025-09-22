import { 
  uploadText, 
  uploadTextFile, 
  getTextProfile, 
  getTextRaw, 
  deleteText,
  uploadImage, 
  createSampleImage,
  getImageInfo,
  getImageFace,
  getImageOriginal,
  deleteImage,
  generatePreview,
  getPreviewStatus,
  serveOutputFile,
  checkHealth,
  getDeviceInfo
} from '@/lib/api'

// Mock fetch
global.fetch = jest.fn()

describe('API Functions', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Text API', () => {
    it('uploadText should make correct API call', async () => {
      const mockResponse = {
        status: 'ok',
        text_id: 'test-id',
        session_id: 'session-id',
        word_count: 10,
        character_count: 50,
        style_profile: {
          vocabulary_richness: 0.5,
          avg_sentence_length: 5.0,
          reading_ease: 70.0,
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
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      })

      const result = await uploadText('Test text content')

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/wizard/text/upload',
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData)
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('uploadTextFile should make correct API call', async () => {
      const mockResponse = {
        status: 'ok',
        text_id: 'test-id',
        session_id: 'session-id',
        word_count: 10,
        character_count: 50,
        style_profile: {},
        files: {}
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      })

      const file = new File(['test content'], 'test.txt', { type: 'text/plain' })
      const result = await uploadTextFile(file)

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/wizard/text/upload-file',
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData)
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('getTextProfile should make correct API call', async () => {
      const mockResponse = {
        status: 'ok',
        text_id: 'test-id',
        profile: {
          vocabulary_richness: 0.5,
          avg_sentence_length: 5.0,
          reading_ease: 70.0,
          tone: {
            positive: 0.3,
            negative: 0.1,
            formal: 0.6,
            casual: 0.4
          }
        }
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      })

      const result = await getTextProfile('test-id')

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/wizard/text/test-id/profile')
      expect(result).toEqual(mockResponse)
    })

    it('getTextRaw should make correct API call', async () => {
      const mockResponse = {
        status: 'ok',
        text_id: 'test-id',
        text: 'Test text content'
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      })

      const result = await getTextRaw('test-id')

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/wizard/text/test-id/raw')
      expect(result).toEqual(mockResponse)
    })

    it('deleteText should make correct API call', async () => {
      const mockResponse = {
        status: 'ok',
        text_id: 'test-id',
        deleted_files: ['file1.txt', 'file2.json']
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      })

      const result = await deleteText('test-id')

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/wizard/text/test-id', {
        method: 'DELETE'
      })
      expect(result).toEqual(mockResponse)
    })

    it('should handle API errors correctly', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ detail: 'Text too short' })
      })

      await expect(uploadText('short')).rejects.toThrow('Text too short')
    })

    it('should handle network errors correctly', async () => {
      ;(fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'))

      await expect(uploadText('test')).rejects.toThrow('Network error')
    })
  })

  describe('Image API', () => {
    it('uploadImage should make correct API call', async () => {
      const mockResponse = {
        status: 'ok',
        image_id: 'test-id',
        session_id: 'session-id',
        face_detected: true,
        original_size: [800, 600],
        output_size: [512, 512],
        files: {
          original: '/data/uploads/test.png',
          face_ref: '/data/portraits/test_face.png'
        }
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      })

      const file = new File(['test image'], 'test.png', { type: 'image/png' })
      const result = await uploadImage(file)

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/wizard/image/upload',
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData)
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('createSampleImage should make correct API call', async () => {
      const mockResponse = {
        status: 'ok',
        image_id: 'sample-id',
        session_id: 'session-id',
        face_detected: true,
        original_size: [512, 512],
        output_size: [512, 512],
        files: {
          original: '/data/uploads/sample.png',
          face_ref: '/data/portraits/sample_face.png'
        }
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      })

      const result = await createSampleImage(512)

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/wizard/image/sample',
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData)
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('getImageInfo should make correct API call', async () => {
      const mockResponse = {
        status: 'ok',
        image_id: 'test-id',
        face_image: '/data/portraits/test_face.png',
        original_image: '/data/uploads/test.png'
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      })

      const result = await getImageInfo('test-id')

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/wizard/image/test-id/info')
      expect(result).toEqual(mockResponse)
    })

    it('getImageFace should make correct API call', async () => {
      const mockBlob = new Blob(['fake image data'], { type: 'image/png' })
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        blob: () => Promise.resolve(mockBlob)
      })

      const result = await getImageFace('test-id')

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/wizard/image/test-id/face')
      expect(result).toEqual(mockBlob)
    })

    it('getImageOriginal should make correct API call', async () => {
      const mockBlob = new Blob(['fake image data'], { type: 'image/png' })
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        blob: () => Promise.resolve(mockBlob)
      })

      const result = await getImageOriginal('test-id')

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/wizard/image/test-id/original')
      expect(result).toEqual(mockBlob)
    })

    it('deleteImage should make correct API call', async () => {
      const mockResponse = {
        status: 'ok',
        image_id: 'test-id',
        deleted_files: ['file1.png', 'file2.png']
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      })

      const result = await deleteImage('test-id')

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/wizard/image/test-id', {
        method: 'DELETE'
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('Preview API', () => {
    it('generatePreview should make correct API call', async () => {
      const mockResponse = {
        status: 'ok',
        url: '/data/outputs/preview.mp4',
        size_px: 256,
        fps: 12,
        duration_seconds: 5.0
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      })

      const result = await generatePreview('Test prompt', true)

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/preview/generate',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            prompt: 'Test prompt',
            use_sample: true
          })
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('getPreviewStatus should make correct API call', async () => {
      const mockResponse = {
        status: 'completed',
        url: '/data/outputs/preview.mp4'
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      })

      const result = await getPreviewStatus('task-id')

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/preview/status/task-id')
      expect(result).toEqual(mockResponse)
    })

    it('serveOutputFile should make correct API call', async () => {
      const mockBlob = new Blob(['fake video data'], { type: 'video/mp4' })
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        blob: () => Promise.resolve(mockBlob)
      })

      const result = await serveOutputFile('preview.mp4')

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/data/outputs/preview.mp4')
      expect(result).toEqual(mockBlob)
    })
  })

  describe('Health API', () => {
    it('checkHealth should make correct API call', async () => {
      const mockResponse = {
        ok: true,
        timestamp: '2023-01-01T00:00:00Z',
        version: '0.1.0'
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      })

      const result = await checkHealth()

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/healthz')
      expect(result).toEqual(mockResponse)
    })

    it('getDeviceInfo should make correct API call', async () => {
      const mockResponse = {
        device: {
          device: 'cpu',
          cuda_available: false,
          cuda_device_count: 0
        },
        memory: {
          total: 8000000000,
          available: 4000000000
        },
        timestamp: '2023-01-01T00:00:00Z'
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      })

      const result = await getDeviceInfo()

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/device')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('Error Handling', () => {
    it('should handle 404 errors', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: () => Promise.resolve({ detail: 'Not found' })
      })

      await expect(getTextProfile('nonexistent')).rejects.toThrow('Not found')
    })

    it('should handle 422 validation errors', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 422,
        json: () => Promise.resolve({ detail: 'Validation error' })
      })

      await expect(uploadText('')).rejects.toThrow('Validation error')
    })

    it('should handle 400 client errors', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ detail: 'Bad request' })
      })

      await expect(uploadImage(new File([''], 'test.txt', { type: 'text/plain' }))).rejects.toThrow('Bad request')
    })

    it('should handle 500 server errors', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ detail: 'Internal server error' })
      })

      await expect(uploadText('test')).rejects.toThrow('Internal server error')
    })

    it('should handle network timeouts', async () => {
      ;(fetch as jest.Mock).mockRejectedValueOnce(new Error('Request timeout'))

      await expect(uploadText('test')).rejects.toThrow('Request timeout')
    })

    it('should handle JSON parsing errors', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.reject(new Error('Invalid JSON'))
      })

      await expect(uploadText('test')).rejects.toThrow('Invalid JSON')
    })
  })

  describe('FormData Construction', () => {
    it('should construct FormData correctly for text upload', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ status: 'ok' })
      })

      await uploadText('Test text')

      const call = (fetch as jest.Mock).mock.calls[0]
      const formData = call[1].body as FormData
      
      expect(formData.get('text')).toBe('Test text')
    })

    it('should construct FormData correctly for text file upload', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ status: 'ok' })
      })

      const file = new File(['test content'], 'test.txt', { type: 'text/plain' })
      await uploadTextFile(file)

      const call = (fetch as jest.Mock).mock.calls[0]
      const formData = call[1].body as FormData
      
      expect(formData.get('file')).toBe(file)
    })

    it('should construct FormData correctly for image upload', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ status: 'ok' })
      })

      const file = new File(['test image'], 'test.png', { type: 'image/png' })
      await uploadImage(file)

      const call = (fetch as jest.Mock).mock.calls[0]
      const formData = call[1].body as FormData
      
      expect(formData.get('file')).toBe(file)
    })

    it('should construct FormData correctly for sample image creation', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ status: 'ok' })
      })

      await createSampleImage(512)

      const call = (fetch as jest.Mock).mock.calls[0]
      const formData = call[1].body as FormData
      
      expect(formData.get('target_size')).toBe('512')
    })
  })

  describe('URL Construction', () => {
    it('should use correct base URL for all endpoints', async () => {
      ;(fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ status: 'ok' })
      })

      await uploadText('test')
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/wizard/text/upload',
        expect.any(Object)
      )

      await getTextProfile('test-id')
      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/wizard/text/test-id/profile')

      await uploadImage(new File([''], 'test.png', { type: 'image/png' }))
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/wizard/image/upload',
        expect.any(Object)
      )

      await getImageInfo('test-id')
      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/wizard/image/test-id/info')

      await generatePreview('test', true)
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/preview/generate',
        expect.any(Object)
      )

      await checkHealth()
      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/healthz')
    })
  })
})
