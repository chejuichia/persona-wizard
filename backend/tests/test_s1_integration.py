"""Integration tests for S1 upload workflows."""

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


@pytest.fixture
def sample_text():
    """Create sample text for testing."""
    return "This is a comprehensive test text for style analysis. It contains multiple sentences with varying lengths and complexity. Some sentences are short. Others are much longer and contain more complex grammatical structures that should be analyzed by the style profiling system."


def test_complete_s1_workflow(sample_image, sample_text):
    """Test complete S1 workflow: text upload -> image upload -> preview generation."""
    
    # Step 1: Upload text
    text_response = client.post("/wizard/text/upload", data={"text": sample_text})
    assert text_response.status_code == 200
    text_data = text_response.json()
    text_id = text_data["text_id"]
    
    # Verify text upload
    assert text_data["status"] == "ok"
    assert text_data["word_count"] > 0
    assert "style_profile" in text_data
    
    # Step 2: Upload image
    with open(sample_image, 'rb') as f:
        image_response = client.post(
            "/wizard/image/upload",
            files={"file": ("test.png", f, "image/png")}
        )
    
    assert image_response.status_code == 200
    image_data = image_response.json()
    image_id = image_data["image_id"]
    
    # Verify image upload
    assert image_data["status"] == "ok"
    assert "face_detected" in image_data
    assert "files" in image_data
    
    # Step 3: Generate preview (if available)
    preview_response = client.post("/preview/generate", json={
        "prompt": "Hello, this is a test preview",
        "use_sample": True
    })
    
    # Preview might succeed or fail depending on sample files
    assert preview_response.status_code in [200, 404]
    
    # Step 4: Verify both uploads are accessible
    text_profile_response = client.get(f"/wizard/text/{text_id}/profile")
    assert text_profile_response.status_code == 200
    
    image_info_response = client.get(f"/wizard/image/{image_id}/info")
    assert image_info_response.status_code == 200
    
    # Step 5: Clean up
    text_delete_response = client.delete(f"/wizard/text/{text_id}")
    assert text_delete_response.status_code == 200
    
    image_delete_response = client.delete(f"/wizard/image/{image_id}")
    assert image_delete_response.status_code == 200


def test_s1_text_workflow_variations():
    """Test various text upload scenarios."""
    
    # Test 1: Short text (should fail)
    short_response = client.post("/wizard/text/upload", data={"text": "short"})
    assert short_response.status_code == 422
    
    # Test 2: Long text (should succeed)
    long_text = "This is a very long text. " * 100
    long_response = client.post("/wizard/text/upload", data={"text": long_text})
    assert long_response.status_code == 200
    
    # Test 3: Multilingual text
    multilingual_text = "Hello world. Hola mundo. Bonjour le monde. Hallo Welt."
    multi_response = client.post("/wizard/text/upload", data={"text": multilingual_text})
    assert multi_response.status_code == 200
    
    # Test 4: Text with special characters
    special_text = "Hello! @#$%^&*()_+-=[]{}|;':\",./<>?`~ 😀🎉🚀"
    special_response = client.post("/wizard/text/upload", data={"text": special_text})
    assert special_response.status_code == 200
    
    # Clean up successful uploads
    for response in [long_response, multi_response, special_response]:
        if response.status_code == 200:
            text_id = response.json()["text_id"]
            client.delete(f"/wizard/text/{text_id}")


def test_s1_image_workflow_variations(sample_image):
    """Test various image upload scenarios."""
    
    # Test 1: Valid image
    with open(sample_image, 'rb') as f:
        valid_response = client.post(
            "/wizard/image/upload",
            files={"file": ("test.png", f, "image/png")}
        )
    assert valid_response.status_code == 200
    
    # Test 2: Invalid file type
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b"not an image")
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            invalid_response = client.post(
                "/wizard/image/upload",
                files={"file": ("test.txt", f, "text/plain")}
            )
        assert invalid_response.status_code == 400
    finally:
        Path(temp_path).unlink()
    
    # Test 3: Sample image creation
    sample_response = client.post("/wizard/image/sample", data={"target_size": "256"})
    assert sample_response.status_code == 200
    
    # Clean up successful uploads
    if valid_response.status_code == 200:
        image_id = valid_response.json()["image_id"]
        client.delete(f"/wizard/image/{image_id}")
    
    if sample_response.status_code == 200:
        sample_id = sample_response.json()["image_id"]
        client.delete(f"/wizard/image/{sample_id}")


def test_s1_concurrent_uploads():
    """Test concurrent text and image uploads."""
    import threading
    import time
    
    results = []
    errors = []
    
    def upload_text(text, index):
        try:
            response = client.post("/wizard/text/upload", data={"text": text})
            results.append(("text", index, response.status_code))
        except Exception as e:
            errors.append(("text", index, str(e)))
    
    def upload_image(image_path, index):
        try:
            with open(image_path, 'rb') as f:
                response = client.post(
                    "/wizard/image/upload",
                    files={"file": (f"test{index}.png", f, "image/png")}
                )
            results.append(("image", index, response.status_code))
        except Exception as e:
            errors.append(("image", index, str(e)))
    
    # Create test image
    img = Image.new('RGB', (100, 100), color='blue')
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        img.save(f.name, 'PNG')
        temp_path = f.name
    
    try:
        # Create threads for concurrent uploads
        threads = []
        
        # Text uploads
        for i in range(3):
            text = f"This is concurrent test text number {i}. " * 10
            thread = threading.Thread(target=upload_text, args=(text, i))
            threads.append(thread)
            thread.start()
        
        # Image uploads
        for i in range(2):
            thread = threading.Thread(target=upload_image, args=(temp_path, i))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        
        # All should succeed
        for upload_type, index, status_code in results:
            assert status_code == 200, f"{upload_type} upload {index} failed with status {status_code}"
        
        # Clean up
        for upload_type, index, status_code in results:
            if status_code == 200:
                if upload_type == "text":
                    # Get text_id from the response (would need to store it)
                    pass  # Skip cleanup for this test
                elif upload_type == "image":
                    # Get image_id from the response (would need to store it)
                    pass  # Skip cleanup for this test
    
    finally:
        Path(temp_path).unlink()


def test_s1_error_handling():
    """Test error handling in S1 workflows."""
    
    # Test 1: Text upload with empty data
    empty_response = client.post("/wizard/text/upload", data={})
    assert empty_response.status_code == 422
    
    # Test 2: Image upload without file
    no_file_response = client.post("/wizard/image/upload")
    assert no_file_response.status_code == 422
    
    # Test 3: Access non-existent resources
    text_profile_response = client.get("/wizard/text/nonexistent/profile")
    assert text_profile_response.status_code == 404
    
    image_info_response = client.get("/wizard/image/nonexistent/info")
    assert image_info_response.status_code == 404
    
    # Test 4: Delete non-existent resources
    text_delete_response = client.delete("/wizard/text/nonexistent")
    assert text_delete_response.status_code == 404
    
    image_delete_response = client.delete("/wizard/image/nonexistent")
    assert image_delete_response.status_code == 404


def test_s1_file_upload_workflows():
    """Test file upload workflows for both text and images."""
    
    # Test text file upload
    text_content = "This is a test file for text upload workflow."
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(text_content)
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            text_file_response = client.post(
                "/wizard/text/upload-file",
                files={"file": ("test.txt", f, "text/plain")}
            )
        
        assert text_file_response.status_code == 200
        text_data = text_file_response.json()
        text_id = text_data["text_id"]
        
        # Verify the uploaded text
        raw_response = client.get(f"/wizard/text/{text_id}/raw")
        assert raw_response.status_code == 200
        assert raw_response.json()["text"] == text_content
        
        # Clean up
        client.delete(f"/wizard/text/{text_id}")
        
    finally:
        Path(temp_path).unlink()
    
    # Test image file upload
    img = Image.new('RGB', (150, 150), color='green')
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        img.save(f.name, 'PNG')
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            image_file_response = client.post(
                "/wizard/image/upload",
                files={"file": ("test.png", f, "image/png")}
            )
        
        assert image_file_response.status_code == 200
        image_data = image_file_response.json()
        image_id = image_data["image_id"]
        
        # Verify the uploaded image
        face_response = client.get(f"/wizard/image/{image_id}/face")
        assert face_response.status_code == 200
        
        # Clean up
        client.delete(f"/wizard/image/{image_id}")
        
    finally:
        Path(temp_path).unlink()


def test_s1_data_persistence():
    """Test that uploaded data persists across requests."""
    
    # Upload text
    text_content = "This text should persist across requests."
    text_response = client.post("/wizard/text/upload", data={"text": text_content})
    assert text_response.status_code == 200
    text_id = text_response.json()["text_id"]
    
    # Upload image
    img = Image.new('RGB', (100, 100), color='purple')
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        img.save(f.name, 'PNG')
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            image_response = client.post(
                "/wizard/image/upload",
                files={"file": ("test.png", f, "image/png")}
            )
        
        assert image_response.status_code == 200
        image_id = image_response.json()["image_id"]
        
        # Verify persistence - make multiple requests
        for _ in range(3):
            # Check text
            text_profile_response = client.get(f"/wizard/text/{text_id}/profile")
            assert text_profile_response.status_code == 200
            
            text_raw_response = client.get(f"/wizard/text/{text_id}/raw")
            assert text_raw_response.status_code == 200
            assert text_raw_response.json()["text"] == text_content
            
            # Check image
            image_info_response = client.get(f"/wizard/image/{image_id}/info")
            assert image_info_response.status_code == 200
            
            image_face_response = client.get(f"/wizard/image/{image_id}/face")
            assert image_face_response.status_code == 200
        
        # Clean up
        client.delete(f"/wizard/text/{text_id}")
        client.delete(f"/wizard/image/{image_id}")
        
    finally:
        Path(temp_path).unlink()


def test_s1_api_consistency():
    """Test API consistency across different endpoints."""
    
    # Upload text and image
    text_content = "API consistency test text."
    text_response = client.post("/wizard/text/upload", data={"text": text_content})
    assert text_response.status_code == 200
    text_id = text_response.json()["text_id"]
    
    img = Image.new('RGB', (100, 100), color='orange')
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        img.save(f.name, 'PNG')
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            image_response = client.post(
                "/wizard/image/upload",
                files={"file": ("test.png", f, "image/png")}
            )
        
        assert image_response.status_code == 200
        image_id = image_response.json()["image_id"]
        
        # Test consistent response formats
        text_profile = client.get(f"/wizard/text/{text_id}/profile").json()
        assert "status" in text_profile
        assert "text_id" in text_profile
        assert "profile" in text_profile
        
        image_info = client.get(f"/wizard/image/{image_id}/info").json()
        assert "status" in image_info
        assert "image_id" in image_info
        assert "face_image" in image_info
        assert "original_image" in image_info
        
        # Test consistent error formats
        text_error = client.get("/wizard/text/nonexistent/profile").json()
        assert "detail" in text_error
        
        image_error = client.get("/wizard/image/nonexistent/info").json()
        assert "detail" in image_error
        
        # Clean up
        client.delete(f"/wizard/text/{text_id}")
        client.delete(f"/wizard/image/{image_id}")
        
    finally:
        Path(temp_path).unlink()
