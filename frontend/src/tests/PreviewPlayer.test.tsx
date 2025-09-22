import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PreviewPlayer } from '@/components/PreviewPlayer'

// Mock fetch
global.fetch = jest.fn()

describe('PreviewPlayer', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(<PreviewPlayer url="http://example.com/video.mp4" />)
    expect(screen.getByRole('video')).toBeInTheDocument()
  })

  it('renders with custom props', () => {
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        width={400}
        height={300}
        className="custom-class"
      />
    )
    
    const video = screen.getByRole('video')
    expect(video).toHaveAttribute('src', 'http://example.com/video.mp4')
    expect(video).toHaveAttribute('width', '400')
    expect(video).toHaveAttribute('height', '300')
    expect(video).toHaveClass('custom-class')
  })

  it('handles video load events', async () => {
    const onLoadMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onLoad={onLoadMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.loadedData(video)
    
    expect(onLoadMock).toHaveBeenCalled()
  })

  it('handles video error events', async () => {
    const onErrorMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onError={onErrorMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.error(video)
    
    expect(onErrorMock).toHaveBeenCalled()
  })

  it('handles video play events', async () => {
    const onPlayMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onPlay={onPlayMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.play(video)
    
    expect(onPlayMock).toHaveBeenCalled()
  })

  it('handles video pause events', async () => {
    const onPauseMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onPause={onPauseMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.pause(video)
    
    expect(onPauseMock).toHaveBeenCalled()
  })

  it('handles video ended events', async () => {
    const onEndedMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onEnded={onEndedMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.ended(video)
    
    expect(onEndedMock).toHaveBeenCalled()
  })

  it('applies default attributes', () => {
    render(<PreviewPlayer url="http://example.com/video.mp4" />)
    
    const video = screen.getByRole('video')
    expect(video).toHaveAttribute('controls')
    expect(video).toHaveAttribute('preload', 'metadata')
  })

  it('applies custom attributes', () => {
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        autoPlay
        muted
        loop
        preload="auto"
      />
    )
    
    const video = screen.getByRole('video')
    expect(video).toHaveAttribute('autoPlay')
    expect(video).toHaveAttribute('muted')
    expect(video).toHaveAttribute('loop')
    expect(video).toHaveAttribute('preload', 'auto')
  })

  it('handles missing url gracefully', () => {
    render(<PreviewPlayer url="" />)
    
    const video = screen.getByRole('video')
    expect(video).toHaveAttribute('src', '')
  })

  it('handles null url gracefully', () => {
    render(<PreviewPlayer url={null as any} />)
    
    const video = screen.getByRole('video')
    expect(video).toHaveAttribute('src', '')
  })

  it('forwards ref correctly', () => {
    const ref = jest.fn()
    render(<PreviewPlayer url="http://example.com/video.mp4" ref={ref} />)
    
    expect(ref).toHaveBeenCalled()
  })

  it('handles video time update events', async () => {
    const onTimeUpdateMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onTimeUpdate={onTimeUpdateMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.timeUpdate(video)
    
    expect(onTimeUpdateMock).toHaveBeenCalled()
  })

  it('handles video seeking events', async () => {
    const onSeekingMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onSeeking={onSeekingMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.seeking(video)
    
    expect(onSeekingMock).toHaveBeenCalled()
  })

  it('handles video seeked events', async () => {
    const onSeekedMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onSeeked={onSeekedMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.seeked(video)
    
    expect(onSeekedMock).toHaveBeenCalled()
  })

  it('handles video volume change events', async () => {
    const onVolumeChangeMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onVolumeChange={onVolumeChangeMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.volumeChange(video)
    
    expect(onVolumeChangeMock).toHaveBeenCalled()
  })

  it('handles video rate change events', async () => {
    const onRateChangeMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onRateChange={onRateChangeMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.rateChange(video)
    
    expect(onRateChangeMock).toHaveBeenCalled()
  })

  it('handles video waiting events', async () => {
    const onWaitingMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onWaiting={onWaitingMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.waiting(video)
    
    expect(onWaitingMock).toHaveBeenCalled()
  })

  it('handles video can play events', async () => {
    const onCanPlayMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onCanPlay={onCanPlayMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.canPlay(video)
    
    expect(onCanPlayMock).toHaveBeenCalled()
  })

  it('handles video can play through events', async () => {
    const onCanPlayThroughMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onCanPlayThrough={onCanPlayThroughMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.canPlayThrough(video)
    
    expect(onCanPlayThroughMock).toHaveBeenCalled()
  })

  it('handles video duration change events', async () => {
    const onDurationChangeMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onDurationChange={onDurationChangeMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.durationChange(video)
    
    expect(onDurationChangeMock).toHaveBeenCalled()
  })

  it('handles video load start events', async () => {
    const onLoadStartMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onLoadStart={onLoadStartMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.loadStart(video)
    
    expect(onLoadStartMock).toHaveBeenCalled()
  })

  it('handles video progress events', async () => {
    const onProgressMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onProgress={onProgressMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.progress(video)
    
    expect(onProgressMock).toHaveBeenCalled()
  })

  it('handles video suspend events', async () => {
    const onSuspendMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onSuspend={onSuspendMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.suspend(video)
    
    expect(onSuspendMock).toHaveBeenCalled()
  })

  it('handles video abort events', async () => {
    const onAbortMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onAbort={onAbortMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.abort(video)
    
    expect(onAbortMock).toHaveBeenCalled()
  })

  it('handles video emptied events', async () => {
    const onEmptiedMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onEmptied={onEmptiedMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.emptied(video)
    
    expect(onEmptiedMock).toHaveBeenCalled()
  })

  it('handles video stalled events', async () => {
    const onStalledMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onStalled={onStalledMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.stalled(video)
    
    expect(onStalledMock).toHaveBeenCalled()
  })

  it('handles video loaded metadata events', async () => {
    const onLoadedMetadataMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onLoadedMetadata={onLoadedMetadataMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.loadedMetadata(video)
    
    expect(onLoadedMetadataMock).toHaveBeenCalled()
  })

  it('handles video loaded data events', async () => {
    const onLoadedDataMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onLoadedData={onLoadedDataMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.loadedData(video)
    
    expect(onLoadedDataMock).toHaveBeenCalled()
  })

  it('handles video resize events', async () => {
    const onResizeMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onResize={onResizeMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.resize(video)
    
    expect(onResizeMock).toHaveBeenCalled()
  })

  it('handles video encrypted events', async () => {
    const onEncryptedMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onEncrypted={onEncryptedMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.encrypted(video)
    
    expect(onEncryptedMock).toHaveBeenCalled()
  })

  it('handles video waiting for key events', async () => {
    const onWaitingForKeyMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onWaitingForKey={onWaitingForKeyMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.waitingForKey(video)
    
    expect(onWaitingForKeyMock).toHaveBeenCalled()
  })

  it('handles video key error events', async () => {
    const onKeyErrorMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onKeyError={onKeyErrorMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.keyError(video)
    
    expect(onKeyErrorMock).toHaveBeenCalled()
  })

  it('handles video key added events', async () => {
    const onKeyAddedMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onKeyAdded={onKeyAddedMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.keyAdded(video)
    
    expect(onKeyAddedMock).toHaveBeenCalled()
  })

  it('handles video key message events', async () => {
    const onKeyMessageMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onKeyMessage={onKeyMessageMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.keyMessage(video)
    
    expect(onKeyMessageMock).toHaveBeenCalled()
  })

  it('handles video key status change events', async () => {
    const onKeyStatusChangeMock = jest.fn()
    render(
      <PreviewPlayer 
        url="http://example.com/video.mp4"
        onKeyStatusChange={onKeyStatusChangeMock}
      />
    )
    
    const video = screen.getByRole('video')
    fireEvent.keyStatusChange(video)
    
    expect(onKeyStatusChangeMock).toHaveBeenCalled()
  })
})
