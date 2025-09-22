"""Tests for image upload functionality."""

import pytest
import tempfile
from pathlib import Path
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def sample_image():
    """Create a sample image for testing."""
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        img.save(f.name, 'PNG')
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink()


def test_upload_image_success(sample_image):
    """Test successful image upload."""
    with open(sample_image, 'rb') as f:
        response = client.post(
            "/wizard/image/upload",
            files={"file": ("test.png", f, "image/png")}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert "image_id" in data
    assert "session_id" in data
    assert "face_detected" in data
    assert "original_size" in data
    assert "output_size" in data
    assert "files" in data


def test_upload_image_invalid_type():
    """Test image upload with invalid file type."""
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b"not an image")
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            response = client.post(
                "/wizard/image/upload",
                files={"file": ("test.txt", f, "text/plain")}
            )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        
    finally:
        Path(temp_path).unlink()


def test_upload_image_too_large():
    """Test image upload with file too large."""
    # Create a large file (simulate)
    large_data = b"x" * (11 * 1024 * 1024)  # 11MB
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        f.write(large_data)
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            response = client.post(
                "/wizard/image/upload",
                files={"file": ("large.png", f, "image/png")}
            )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        
    finally:
        Path(temp_path).unlink()


def test_get_face_image(sample_image):
    """Test getting prepared face image."""
    # First upload an image
    with open(sample_image, 'rb') as f:
        upload_response = client.post(
            "/wizard/image/upload",
            files={"file": ("test.png", f, "image/png")}
        )
    
    assert upload_response.status_code == 200
    image_id = upload_response.json()["image_id"]
    
    # Get the face image
    response = client.get(f"/wizard/image/{image_id}/face")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


def test_get_face_image_not_found():
    """Test getting face image for non-existent image."""
    response = client.get("/wizard/image/nonexistent/face")
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_get_original_image(sample_image):
    """Test getting original uploaded image."""
    # First upload an image
    with open(sample_image, 'rb') as f:
        upload_response = client.post(
            "/wizard/image/upload",
            files={"file": ("test.png", f, "image/png")}
        )
    
    assert upload_response.status_code == 200
    image_id = upload_response.json()["image_id"]
    
    # Get the original image
    response = client.get(f"/wizard/image/{image_id}/original")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


def test_get_image_info(sample_image):
    """Test getting image processing information."""
    # First upload an image
    with open(sample_image, 'rb') as f:
        upload_response = client.post(
            "/wizard/image/upload",
            files={"file": ("test.png", f, "image/png")}
        )
    
    assert upload_response.status_code == 200
    image_id = upload_response.json()["image_id"]
    
    # Get image info
    response = client.get(f"/wizard/image/{image_id}/info")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert data["image_id"] == image_id
    assert "face_image" in data
    assert "original_image" in data


def test_delete_image(sample_image):
    """Test deleting uploaded image."""
    # First upload an image
    with open(sample_image, 'rb') as f:
        upload_response = client.post(
            "/wizard/image/upload",
            files={"file": ("test.png", f, "image/png")}
        )
    
    assert upload_response.status_code == 200
    image_id = upload_response.json()["image_id"]
    
    # Delete the image
    response = client.delete(f"/wizard/image/{image_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert data["image_id"] == image_id
    assert "deleted_files" in data
    
    # Try to get the face image (should fail)
    face_response = client.get(f"/wizard/image/{image_id}/face")
    assert face_response.status_code == 404


def test_delete_image_not_found():
    """Test deleting non-existent image."""
    response = client.delete("/wizard/image/nonexistent")
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_create_sample_image():
    """Test creating a sample image."""
    response = client.post("/wizard/image/sample", data={"target_size": "512"})
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert "image_id" in data
    assert "session_id" in data
    assert data["face_detected"] is True
    assert data["output_size"] == [512, 512]
    assert "files" in data


def test_create_sample_image_invalid_size():
    """Test creating sample image with invalid size."""
    response = client.post("/wizard/image/sample", data={"target_size": "invalid"})
    
    assert response.status_code == 422  # Validation error


def test_create_sample_image_missing_size():
    """Test creating sample image without size parameter."""
    response = client.post("/wizard/image/sample")
    
    # The API might have a default size, so accept either 200 or 422
    assert response.status_code in [200, 422]


def test_upload_image_corrupted():
    """Test uploading a corrupted image file."""
    # Create a file that looks like an image but is corrupted
    corrupted_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        f.write(corrupted_data)
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            response = client.post(
                "/wizard/image/upload",
                files={"file": ("corrupted.png", f, "image/png")}
            )
        
        # Should either succeed with face_detected=False or fail gracefully
        assert response.status_code in [200, 400]
        
    finally:
        Path(temp_path).unlink()


def test_upload_image_unsupported_format():
    """Test uploading image with unsupported format."""
    # Create a GIF file (if not supported)
    gif_data = b'GIF87a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
    
    with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as f:
        f.write(gif_data)
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            response = client.post(
                "/wizard/image/upload",
                files={"file": ("test.gif", f, "image/gif")}
            )
        
        # Should either succeed or fail with appropriate error
        assert response.status_code in [200, 400]
        
    finally:
        Path(temp_path).unlink()


def test_upload_image_no_face_detected():
    """Test uploading image with no face detected."""
    # Create a simple image with no face (just a solid color)
    img = Image.new('RGB', (200, 200), color='blue')
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        img.save(f.name, 'PNG')
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            response = client.post(
                "/wizard/image/upload",
                files={"file": ("noface.png", f, "image/png")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["face_detected"] is False
        assert "files" in data
        
    finally:
        Path(temp_path).unlink()


def test_upload_image_multiple_faces():
    """Test uploading image with multiple faces."""
    # Create a simple image that might have multiple faces (or at least test the path)
    img = Image.new('RGB', (400, 200), color='white')
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        img.save(f.name, 'PNG')
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            response = client.post(
                "/wizard/image/upload",
                files={"file": ("multiface.png", f, "image/png")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "face_detected" in data
        assert "files" in data
        
    finally:
        Path(temp_path).unlink()


def test_upload_image_very_small():
    """Test uploading very small image."""
    img = Image.new('RGB', (10, 10), color='red')
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        img.save(f.name, 'PNG')
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            response = client.post(
                "/wizard/image/upload",
                files={"file": ("tiny.png", f, "image/png")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "face_detected" in data
        assert "files" in data
        
    finally:
        Path(temp_path).unlink()


def test_upload_image_very_large_dimensions():
    """Test uploading image with very large dimensions."""
    img = Image.new('RGB', (5000, 5000), color='red')
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        img.save(f.name, 'PNG')
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            response = client.post(
                "/wizard/image/upload",
                files={"file": ("huge.png", f, "image/png")}
            )
        
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 400]
        
    finally:
        Path(temp_path).unlink()


def test_upload_image_missing_file():
    """Test uploading without file parameter."""
    response = client.post("/wizard/image/upload")
    assert response.status_code == 422  # Validation error


def test_upload_image_empty_filename():
    """Test uploading with empty filename."""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        f.write(b"fake image data")
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            response = client.post(
                "/wizard/image/upload",
                files={"file": ("", f, "image/png")}
            )
        
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 400, 422]
        
    finally:
        Path(temp_path).unlink()


def test_get_face_image_different_formats():
    """Test getting face image in different formats."""
    # Upload an image first
    img = Image.new('RGB', (100, 100), color='red')
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        img.save(f.name, 'PNG')
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            upload_response = client.post(
                "/wizard/image/upload",
                files={"file": ("test.png", f, "image/png")}
            )
        
        assert upload_response.status_code == 200
        image_id = upload_response.json()["image_id"]
        
        # Test different format requests
        for format_type in ["png", "jpg", "webp"]:
            response = client.get(f"/wizard/image/{image_id}/face?format={format_type}")
            # Should either succeed or return appropriate error
            assert response.status_code in [200, 400, 422]
        
    finally:
        Path(temp_path).unlink()


def test_image_workflow_complete():
    """Test complete image workflow: upload -> get info -> get face -> get original -> delete."""
    # Upload
    img = Image.new('RGB', (100, 100), color='red')
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        img.save(f.name, 'PNG')
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            upload_response = client.post(
                "/wizard/image/upload",
                files={"file": ("test.png", f, "image/png")}
            )
        
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        image_id = upload_data["image_id"]
        
        # Get info
        info_response = client.get(f"/wizard/image/{image_id}/info")
        assert info_response.status_code == 200
        
        # Get face
        face_response = client.get(f"/wizard/image/{image_id}/face")
        assert face_response.status_code == 200
        
        # Get original
        original_response = client.get(f"/wizard/image/{image_id}/original")
        assert original_response.status_code == 200
        
        # Delete
        delete_response = client.delete(f"/wizard/image/{image_id}")
        assert delete_response.status_code == 200
        
        # Verify deletion
        face_response_after = client.get(f"/wizard/image/{image_id}/face")
        assert face_response_after.status_code == 404
        
    finally:
        Path(temp_path).unlink()
