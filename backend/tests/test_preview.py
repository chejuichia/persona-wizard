"""Tests for preview endpoints."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from app.main import app
from app.core.config import settings

client = TestClient(app)


@pytest.fixture
def sample_files():
    """Create sample files for testing."""
    # Create sample image
    sample_image = settings.data_dir / "portraits" / "sample_face.png"
    sample_image.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a simple 1x1 pixel PNG
    from PIL import Image
    img = Image.new('RGB', (100, 100), color='red')
    img.save(sample_image)
    
    # Create sample audio
    sample_audio = settings.data_dir / "audio" / "hello_2s.wav"
    sample_audio.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a simple audio file (1 second of silence)
    import numpy as np
    import soundfile as sf
    sample_rate = 16000
    duration = 2.0
    audio_data = np.zeros(int(sample_rate * duration))
    sf.write(str(sample_audio), audio_data, sample_rate)
    
    yield sample_image, sample_audio
    
    # Cleanup
    if sample_image.exists():
        sample_image.unlink()
    if sample_audio.exists():
        sample_audio.unlink()


def test_generate_preview(sample_files):
    """Test preview generation endpoint."""
    sample_image, sample_audio = sample_files
    
    response = client.post("/preview/generate", json={
        "prompt": "Hello, this is a test preview",
        "use_sample": True
    })
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert "url" in data
    assert data["size_px"] == 256
    assert data["fps"] == 12
    assert data["duration_seconds"] > 0


def test_generate_preview_missing_files():
    """Test preview generation with missing sample files."""
    response = client.post("/preview/generate", json={
        "prompt": "Hello, this is a test preview",
        "use_sample": True
    })
    
    # Should return 404 for missing sample files
    assert response.status_code == 404


def test_serve_output_file(sample_files):
    """Test serving output files."""
    sample_image, sample_audio = sample_files
    
    # First generate a preview
    response = client.post("/preview/generate", json={
        "prompt": "Hello, this is a test preview",
        "use_sample": True
    })
    
    assert response.status_code == 200
    data = response.json()
    output_url = data["url"]
    
    # Extract filename from URL
    filename = output_url.split("/")[-1]
    
    # Try to serve the file
    response = client.get(f"/data/outputs/{filename}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "video/mp4"


def test_serve_nonexistent_file():
    """Test serving non-existent file."""
    response = client.get("/data/outputs/nonexistent.mp4")
    assert response.status_code == 404


def test_preview_status():
    """Test preview status endpoint."""
    # Test with non-existent task ID
    response = client.get("/preview/status/nonexistent")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "not_found"
    assert data["url"] is None
