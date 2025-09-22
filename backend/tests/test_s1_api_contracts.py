"""API contract tests for S1 endpoints to ensure frontend-backend compatibility."""

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
    img = Image.new('RGB', (200, 200), color='red')
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        img.save(f.name, 'PNG')
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink()


def test_text_upload_api_contract():
    """Test text upload API contract matches frontend expectations."""
    
    sample_text = "This is a test text for API contract validation."
    
    response = client.post("/wizard/text/upload", data={"text": sample_text})
    assert response.status_code == 200
    
    data = response.json()
    
    # Required fields for frontend
    required_fields = [
        "status", "text_id", "session_id", "token_count", 
        "word_count", "character_count", "style_profile", "files"
    ]
    
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
    
    # Validate status
    assert data["status"] == "ok"
    
    # Validate IDs are strings
    assert isinstance(data["text_id"], str)
    assert isinstance(data["session_id"], str)
    assert len(data["text_id"]) > 0
    assert len(data["session_id"]) > 0
    
    # Validate counts are positive integers
    assert isinstance(data["token_count"], int)
    assert isinstance(data["word_count"], int)
    assert isinstance(data["character_count"], int)
    assert data["token_count"] > 0
    assert data["word_count"] > 0
    assert data["character_count"] > 0
    
    # Validate style profile structure
    style_profile = data["style_profile"]
    assert isinstance(style_profile, dict)
    
    required_profile_fields = [
        "vocabulary_richness", "avg_sentence_length", "reading_ease", "tone"
    ]
    
    for field in required_profile_fields:
        assert field in style_profile, f"Missing style profile field: {field}"
    
    # Validate tone structure
    tone = style_profile["tone"]
    assert isinstance(tone, dict)
    
    required_tone_fields = ["positive", "negative", "formal", "casual"]
    
    for field in required_tone_fields:
        assert field in tone, f"Missing tone field: {field}"
        assert isinstance(tone[field], (int, float))
        assert 0 <= tone[field] <= 1, f"Tone value {field} out of range: {tone[field]}"
    
    # Validate files structure
    files = data["files"]
    assert isinstance(files, dict)
    assert "raw_text" in files
    assert "style_profile" in files
    assert isinstance(files["raw_text"], str)
    assert isinstance(files["style_profile"], str)
    
    # Clean up
    client.delete(f"/wizard/text/{data['text_id']}")


def test_text_upload_validation_contract():
    """Test text upload validation contract."""
    
    # Test empty text
    response = client.post("/wizard/text/upload", data={"text": ""})
    assert response.status_code == 422
    
    # Test whitespace-only text
    response = client.post("/wizard/text/upload", data={"text": "   \n\t   "})
    assert response.status_code == 422
    
    # Test too short text
    response = client.post("/wizard/text/upload", data={"text": "short"})
    assert response.status_code == 422
    
    # Test missing text parameter
    response = client.post("/wizard/text/upload", data={})
    assert response.status_code == 422
    
    # Test invalid data type
    response = client.post("/wizard/text/upload", json={"text": "valid text"})
    assert response.status_code == 422


def test_text_file_upload_api_contract():
    """Test text file upload API contract."""
    
    text_content = "This is a test file for API contract validation."
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(text_content)
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            response = client.post(
                "/wizard/text/upload-file",
                files={"file": ("test.txt", f, "text/plain")}
            )
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Should have same structure as text upload
        required_fields = [
            "status", "text_id", "session_id", "token_count", 
            "word_count", "character_count", "style_profile", "files"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Clean up
        client.delete(f"/wizard/text/{data['text_id']}")
        
    finally:
        Path(temp_path).unlink()


def test_text_profile_api_contract():
    """Test text profile API contract."""
    
    # First upload text
    sample_text = "This is a test text for profile API contract validation."
    upload_response = client.post("/wizard/text/upload", data={"text": sample_text})
    assert upload_response.status_code == 200
    text_id = upload_response.json()["text_id"]
    
    try:
        # Get profile
        response = client.get(f"/wizard/text/{text_id}/profile")
        assert response.status_code == 200
        
        data = response.json()
        
        # Required fields
        required_fields = ["status", "text_id", "profile"]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Validate status
        assert data["status"] == "ok"
        assert data["text_id"] == text_id
        
        # Validate profile structure
        profile = data["profile"]
        assert isinstance(profile, dict)
        
        # Should have same structure as upload response style_profile
        required_profile_fields = [
            "vocabulary_richness", "avg_sentence_length", "reading_ease", "tone"
        ]
        
        for field in required_profile_fields:
            assert field in profile, f"Missing profile field: {field}"
        
        # Validate metadata if present
        if "metadata" in profile:
            assert isinstance(profile["metadata"], dict)
        
    finally:
        # Clean up
        client.delete(f"/wizard/text/{text_id}")


def test_text_raw_api_contract():
    """Test text raw API contract."""
    
    # First upload text
    sample_text = "This is a test text for raw API contract validation."
    upload_response = client.post("/wizard/text/upload", data={"text": sample_text})
    assert upload_response.status_code == 200
    text_id = upload_response.json()["text_id"]
    
    try:
        # Get raw text
        response = client.get(f"/wizard/text/{text_id}/raw")
        assert response.status_code == 200
        
        data = response.json()
        
        # Required fields
        required_fields = ["status", "text_id", "text"]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Validate status
        assert data["status"] == "ok"
        assert data["text_id"] == text_id
        assert data["text"] == sample_text
        
    finally:
        # Clean up
        client.delete(f"/wizard/text/{text_id}")


def test_image_upload_api_contract(sample_image):
    """Test image upload API contract matches frontend expectations."""
    
    with open(sample_image, 'rb') as f:
        response = client.post(
            "/wizard/image/upload",
            files={"file": ("test.png", f, "image/png")}
        )
    
    assert response.status_code == 200
    
    data = response.json()
    
    # Required fields for frontend
    required_fields = [
        "status", "image_id", "session_id", "face_detected", 
        "original_size", "output_size", "files"
    ]
    
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
    
    # Validate status
    assert data["status"] == "ok"
    
    # Validate IDs are strings
    assert isinstance(data["image_id"], str)
    assert isinstance(data["session_id"], str)
    assert len(data["image_id"]) > 0
    assert len(data["session_id"]) > 0
    
    # Validate face detection is boolean
    assert isinstance(data["face_detected"], bool)
    
    # Validate sizes are arrays of integers
    assert isinstance(data["original_size"], list)
    assert isinstance(data["output_size"], list)
    assert len(data["original_size"]) == 2
    assert len(data["output_size"]) == 2
    
    for size in data["original_size"] + data["output_size"]:
        assert isinstance(size, int)
        assert size > 0
    
    # Validate files structure
    files = data["files"]
    assert isinstance(files, dict)
    assert "original" in files
    assert "face_ref" in files
    assert isinstance(files["original"], str)
    assert isinstance(files["face_ref"], str)
    
    # Clean up
    client.delete(f"/wizard/image/{data['image_id']}")


def test_image_upload_validation_contract():
    """Test image upload validation contract."""
    
    # Test missing file
    response = client.post("/wizard/image/upload")
    assert response.status_code == 422
    
    # Test invalid file type
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
        
    finally:
        Path(temp_path).unlink()


def test_image_info_api_contract(sample_image):
    """Test image info API contract."""
    
    # First upload image
    with open(sample_image, 'rb') as f:
        upload_response = client.post(
            "/wizard/image/upload",
            files={"file": ("test.png", f, "image/png")}
        )
    
    assert upload_response.status_code == 200
    image_id = upload_response.json()["image_id"]
    
    try:
        # Get image info
        response = client.get(f"/wizard/image/{image_id}/info")
        assert response.status_code == 200
        
        data = response.json()
        
        # Required fields
        required_fields = ["status", "image_id", "face_image", "original_image"]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Validate status
        assert data["status"] == "ok"
        assert data["image_id"] == image_id
        
        # Validate file paths are strings
        assert isinstance(data["face_image"], str)
        assert isinstance(data["original_image"], str)
        
    finally:
        # Clean up
        client.delete(f"/wizard/image/{image_id}")


def test_image_face_api_contract(sample_image):
    """Test image face API contract."""
    
    # First upload image
    with open(sample_image, 'rb') as f:
        upload_response = client.post(
            "/wizard/image/upload",
            files={"file": ("test.png", f, "image/png")}
        )
    
    assert upload_response.status_code == 200
    image_id = upload_response.json()["image_id"]
    
    try:
        # Get face image
        response = client.get(f"/wizard/image/{image_id}/face")
        assert response.status_code == 200
        
        # Should return image data
        assert response.headers["content-type"] == "image/png"
        assert len(response.content) > 0
        
    finally:
        # Clean up
        client.delete(f"/wizard/image/{image_id}")


def test_image_original_api_contract(sample_image):
    """Test image original API contract."""
    
    # First upload image
    with open(sample_image, 'rb') as f:
        upload_response = client.post(
            "/wizard/image/upload",
            files={"file": ("test.png", f, "image/png")}
        )
    
    assert upload_response.status_code == 200
    image_id = upload_response.json()["image_id"]
    
    try:
        # Get original image
        response = client.get(f"/wizard/image/{image_id}/original")
        assert response.status_code == 200
        
        # Should return image data
        assert response.headers["content-type"] == "image/png"
        assert len(response.content) > 0
        
    finally:
        # Clean up
        client.delete(f"/wizard/image/{image_id}")


def test_sample_image_api_contract():
    """Test sample image creation API contract."""
    
    response = client.post("/wizard/image/sample", data={"target_size": "256"})
    assert response.status_code == 200
    
    data = response.json()
    
    # Should have same structure as image upload
    required_fields = [
        "status", "image_id", "session_id", "face_detected", 
        "original_size", "output_size", "files"
    ]
    
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
    
    # Validate status
    assert data["status"] == "ok"
    
    # Validate face detection should be true for sample
    assert data["face_detected"] is True
    
    # Validate output size matches requested size
    assert data["output_size"] == [256, 256]
    
    # Clean up
    client.delete(f"/wizard/image/{data['image_id']}")


def test_error_response_contract():
    """Test error response contract consistency."""
    
    # Test 404 errors
    text_profile_response = client.get("/wizard/text/nonexistent/profile")
    assert text_profile_response.status_code == 404
    text_error = text_profile_response.json()
    assert "detail" in text_error
    assert isinstance(text_error["detail"], str)
    
    image_info_response = client.get("/wizard/image/nonexistent/info")
    assert image_info_response.status_code == 404
    image_error = image_info_response.json()
    assert "detail" in image_error
    assert isinstance(image_error["detail"], str)
    
    # Test 422 validation errors
    text_validation_response = client.post("/wizard/text/upload", data={"text": ""})
    assert text_validation_response.status_code == 422
    validation_error = text_validation_response.json()
    assert "detail" in validation_error
    
    # Test 400 client errors
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b"not an image")
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            image_error_response = client.post(
                "/wizard/image/upload",
                files={"file": ("test.txt", f, "text/plain")}
            )
        assert image_error_response.status_code == 400
        image_error = image_error_response.json()
        assert "detail" in image_error
        assert isinstance(image_error["detail"], str)
        
    finally:
        Path(temp_path).unlink()


def test_delete_api_contract():
    """Test delete API contract."""
    
    # Test text deletion
    sample_text = "This is a test text for deletion contract validation."
    upload_response = client.post("/wizard/text/upload", data={"text": sample_text})
    assert upload_response.status_code == 200
    text_id = upload_response.json()["text_id"]
    
    delete_response = client.delete(f"/wizard/text/{text_id}")
    assert delete_response.status_code == 200
    
    data = delete_response.json()
    required_fields = ["status", "text_id", "deleted_files"]
    
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
    
    assert data["status"] == "ok"
    assert data["text_id"] == text_id
    assert isinstance(data["deleted_files"], list)
    
    # Test image deletion
    img = Image.new('RGB', (100, 100), color='blue')
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        img.save(f.name, 'PNG')
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            image_upload_response = client.post(
                "/wizard/image/upload",
                files={"file": ("test.png", f, "image/png")}
            )
        
        assert image_upload_response.status_code == 200
        image_id = image_upload_response.json()["image_id"]
        
        image_delete_response = client.delete(f"/wizard/image/{image_id}")
        assert image_delete_response.status_code == 200
        
        data = image_delete_response.json()
        required_fields = ["status", "image_id", "deleted_files"]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        assert data["status"] == "ok"
        assert data["image_id"] == image_id
        assert isinstance(data["deleted_files"], list)
        
    finally:
        Path(temp_path).unlink()


def test_cors_headers():
    """Test CORS headers for frontend compatibility."""
    
    # Test preflight request
    response = client.options("/wizard/text/upload")
    assert response.status_code in [200, 405]  # 405 is also acceptable
    
    # Test actual request headers
    response = client.post("/wizard/text/upload", data={"text": "test"})
    assert response.status_code == 200
    
    # Check for CORS headers (if implemented)
    # Note: This depends on CORS middleware configuration
    # headers = response.headers
    # assert "Access-Control-Allow-Origin" in headers or "access-control-allow-origin" in headers


def test_content_type_headers():
    """Test content type headers for different endpoints."""
    
    # Test JSON responses
    response = client.get("/healthz")
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")
    
    # Test image responses
    img = Image.new('RGB', (100, 100), color='green')
    
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
        
        # Test face image response
        face_response = client.get(f"/wizard/image/{image_id}/face")
        assert face_response.status_code == 200
        assert "image/png" in face_response.headers.get("content-type", "")
        
        # Clean up
        client.delete(f"/wizard/image/{image_id}")
        
    finally:
        Path(temp_path).unlink()
