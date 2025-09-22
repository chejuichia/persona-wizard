"""End-to-end tests for S1 upload workflows."""

import pytest
import tempfile
import time
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
    return "This is a comprehensive test text for end-to-end style analysis. It contains multiple sentences with varying lengths and complexity. Some sentences are short. Others are much longer and contain more complex grammatical structures that should be analyzed by the style profiling system. The text includes different types of punctuation marks, such as commas, semicolons, and periods. It also has some numbers like 123 and 456. The vocabulary ranges from simple words to more sophisticated terms. This should provide a good sample for style analysis."


def test_complete_text_to_image_workflow(sample_text, sample_image):
    """Test complete workflow: text upload -> image upload -> data verification."""
    
    # Step 1: Upload text
    print("Step 1: Uploading text...")
    text_response = client.post("/wizard/text/upload", data={"text": sample_text})
    assert text_response.status_code == 200
    text_data = text_response.json()
    text_id = text_data["text_id"]
    
    print(f"Text uploaded with ID: {text_id}")
    assert text_data["word_count"] > 0
    assert text_data["character_count"] > 0
    assert "style_profile" in text_data
    
    # Step 2: Verify text data persistence
    print("Step 2: Verifying text data persistence...")
    text_profile_response = client.get(f"/wizard/text/{text_id}/profile")
    assert text_profile_response.status_code == 200
    text_profile = text_profile_response.json()
    
    assert text_profile["text_id"] == text_id
    assert "profile" in text_profile
    assert "vocabulary_richness" in text_profile["profile"]
    assert "tone" in text_profile["profile"]
    
    # Step 3: Get raw text
    print("Step 3: Retrieving raw text...")
    text_raw_response = client.get(f"/wizard/text/{text_id}/raw")
    assert text_raw_response.status_code == 200
    text_raw = text_raw_response.json()
    
    assert text_raw["text"] == sample_text
    assert text_raw["text_id"] == text_id
    
    # Step 4: Upload image
    print("Step 4: Uploading image...")
    with open(sample_image, 'rb') as f:
        image_response = client.post(
            "/wizard/image/upload",
            files={"file": ("test.png", f, "image/png")}
        )
    
    assert image_response.status_code == 200
    image_data = image_response.json()
    image_id = image_data["image_id"]
    
    print(f"Image uploaded with ID: {image_id}")
    assert "face_detected" in image_data
    assert "original_size" in image_data
    assert "output_size" in image_data
    assert "files" in image_data
    
    # Step 5: Verify image data persistence
    print("Step 5: Verifying image data persistence...")
    image_info_response = client.get(f"/wizard/image/{image_id}/info")
    assert image_info_response.status_code == 200
    image_info = image_info_response.json()
    
    assert image_info["image_id"] == image_id
    assert "face_image" in image_info
    assert "original_image" in image_info
    
    # Step 6: Get face image
    print("Step 6: Retrieving face image...")
    face_response = client.get(f"/wizard/image/{image_id}/face")
    assert face_response.status_code == 200
    assert face_response.headers["content-type"] == "image/png"
    assert len(face_response.content) > 0
    
    # Step 7: Get original image
    print("Step 7: Retrieving original image...")
    original_response = client.get(f"/wizard/image/{image_id}/original")
    assert original_response.status_code == 200
    assert original_response.headers["content-type"] == "image/png"
    assert len(original_response.content) > 0
    
    # Step 8: Verify both uploads are accessible simultaneously
    print("Step 8: Verifying simultaneous access...")
    for _ in range(3):
        # Check text
        text_check = client.get(f"/wizard/text/{text_id}/profile")
        assert text_check.status_code == 200
        
        # Check image
        image_check = client.get(f"/wizard/image/{image_id}/info")
        assert image_check.status_code == 200
        
        time.sleep(0.1)  # Small delay to simulate real usage
    
    # Step 9: Clean up
    print("Step 9: Cleaning up...")
    text_delete_response = client.delete(f"/wizard/text/{text_id}")
    assert text_delete_response.status_code == 200
    
    image_delete_response = client.delete(f"/wizard/image/{image_id}")
    assert image_delete_response.status_code == 200
    
    # Step 10: Verify deletion
    print("Step 10: Verifying deletion...")
    text_deleted_check = client.get(f"/wizard/text/{text_id}/profile")
    assert text_deleted_check.status_code == 404
    
    image_deleted_check = client.get(f"/wizard/image/{image_id}/info")
    assert image_deleted_check.status_code == 404
    
    print("Complete workflow test passed!")


def test_file_upload_workflow():
    """Test file upload workflow for both text and images."""
    
    # Test text file upload
    print("Testing text file upload...")
    text_content = "This is a test file for end-to-end text upload workflow. It contains multiple sentences to test the complete file processing pipeline."
    
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
        
        # Verify style analysis was performed
        profile_response = client.get(f"/wizard/text/{text_id}/profile")
        assert profile_response.status_code == 200
        profile = profile_response.json()["profile"]
        assert "vocabulary_richness" in profile
        
        # Clean up
        client.delete(f"/wizard/text/{text_id}")
        
    finally:
        Path(temp_path).unlink()
    
    # Test image file upload
    print("Testing image file upload...")
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
        assert face_response.headers["content-type"] == "image/png"
        
        original_response = client.get(f"/wizard/image/{image_id}/original")
        assert original_response.status_code == 200
        assert original_response.headers["content-type"] == "image/png"
        
        # Verify image processing info
        info_response = client.get(f"/wizard/image/{image_id}/info")
        assert info_response.status_code == 200
        info = info_response.json()
        assert "face_image" in info
        assert "original_image" in info
        
        # Clean up
        client.delete(f"/wizard/image/{image_id}")
        
    finally:
        Path(temp_path).unlink()
    
    print("File upload workflow test passed!")


def test_error_recovery_workflow():
    """Test error recovery and handling in workflows."""
    
    print("Testing error recovery workflow...")
    
    # Test 1: Invalid text upload -> recovery
    print("Testing invalid text upload...")
    invalid_text_response = client.post("/wizard/text/upload", data={"text": "short"})
    assert invalid_text_response.status_code == 422
    
    # Should be able to recover with valid text
    valid_text_response = client.post("/wizard/text/upload", data={"text": "This is a valid text for error recovery testing."})
    assert valid_text_response.status_code == 200
    text_id = valid_text_response.json()["text_id"]
    
    # Test 2: Invalid image upload -> recovery
    print("Testing invalid image upload...")
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b"not an image")
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            invalid_image_response = client.post(
                "/wizard/image/upload",
                files={"file": ("test.txt", f, "text/plain")}
            )
        assert invalid_image_response.status_code == 400
        
        # Should be able to recover with valid image
        img = Image.new('RGB', (100, 100), color='blue')
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f2:
            img.save(f2.name, 'PNG')
            temp_path2 = f2.name
        
        try:
            with open(temp_path2, 'rb') as f2:
                valid_image_response = client.post(
                    "/wizard/image/upload",
                    files={"file": ("test.png", f2, "image/png")}
                )
            assert valid_image_response.status_code == 200
            image_id = valid_image_response.json()["image_id"]
            
            # Clean up
            client.delete(f"/wizard/image/{image_id}")
            
        finally:
            Path(temp_path2).unlink()
        
    finally:
        Path(temp_path).unlink()
    
    # Test 3: Access non-existent resources
    print("Testing non-existent resource access...")
    nonexistent_text_response = client.get("/wizard/text/nonexistent/profile")
    assert nonexistent_text_response.status_code == 404
    
    nonexistent_image_response = client.get("/wizard/image/nonexistent/info")
    assert nonexistent_image_response.status_code == 404
    
    # Test 4: Delete non-existent resources
    print("Testing non-existent resource deletion...")
    nonexistent_text_delete = client.delete("/wizard/text/nonexistent")
    assert nonexistent_text_delete.status_code == 404
    
    nonexistent_image_delete = client.delete("/wizard/image/nonexistent")
    assert nonexistent_image_delete.status_code == 404
    
    # Clean up
    client.delete(f"/wizard/text/{text_id}")
    
    print("Error recovery workflow test passed!")


def test_concurrent_workflow():
    """Test concurrent upload and access workflows."""
    
    print("Testing concurrent workflow...")
    
    import threading
    import time
    
    results = []
    errors = []
    
    def upload_text(text, index):
        try:
            response = client.post("/wizard/text/upload", data={"text": text})
            results.append(("text", index, response.status_code, response.json().get("text_id")))
        except Exception as e:
            errors.append(("text", index, str(e)))
    
    def upload_image(image_path, index):
        try:
            with open(image_path, 'rb') as f:
                response = client.post(
                    "/wizard/image/upload",
                    files={"file": (f"test{index}.png", f, "image/png")}
                )
            results.append(("image", index, response.status_code, response.json().get("image_id")))
        except Exception as e:
            errors.append(("image", index, str(e)))
    
    def access_text(text_id, index):
        try:
            response = client.get(f"/wizard/text/{text_id}/profile")
            results.append(("text_access", index, response.status_code))
        except Exception as e:
            errors.append(("text_access", index, str(e)))
    
    def access_image(image_id, index):
        try:
            response = client.get(f"/wizard/image/{image_id}/info")
            results.append(("image_access", index, response.status_code))
        except Exception as e:
            errors.append(("image_access", index, str(e)))
    
    # Create test image
    img = Image.new('RGB', (100, 100), color='purple')
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        img.save(f.name, 'PNG')
        temp_path = f.name
    
    try:
        # Phase 1: Concurrent uploads
        print("Phase 1: Concurrent uploads...")
        threads = []
        
        # Upload texts
        for i in range(3):
            text = f"This is concurrent test text number {i}. " * 20
            thread = threading.Thread(target=upload_text, args=(text, i))
            threads.append(thread)
            thread.start()
        
        # Upload images
        for i in range(2):
            thread = threading.Thread(target=upload_image, args=(temp_path, i))
            threads.append(thread)
            thread.start()
        
        # Wait for uploads to complete
        for thread in threads:
            thread.join()
        
        print(f"Upload results: {len(results)} successful, {len(errors)} errors")
        assert len(errors) == 0, f"Upload errors: {errors}"
        
        # Phase 2: Concurrent access
        print("Phase 2: Concurrent access...")
        access_threads = []
        
        # Access uploaded resources
        for result in results:
            if result[0] == "text" and result[2] == 200:
                thread = threading.Thread(target=access_text, args=(result[3], result[1]))
                access_threads.append(thread)
                thread.start()
            elif result[0] == "image" and result[2] == 200:
                thread = threading.Thread(target=access_image, args=(result[3], result[1]))
                access_threads.append(thread)
                thread.start()
        
        # Wait for access to complete
        for thread in access_threads:
            thread.join()
        
        print(f"Access results: {len([r for r in results if 'access' in r[0]])} successful")
        
        # Phase 3: Cleanup
        print("Phase 3: Cleanup...")
        for result in results:
            if result[0] == "text" and result[2] == 200 and result[3]:
                client.delete(f"/wizard/text/{result[3]}")
            elif result[0] == "image" and result[2] == 200 and result[3]:
                client.delete(f"/wizard/image/{result[3]}")
        
    finally:
        Path(temp_path).unlink()
    
    print("Concurrent workflow test passed!")


def test_sample_generation_workflow():
    """Test sample generation workflow."""
    
    print("Testing sample generation workflow...")
    
    # Test sample image generation
    print("Testing sample image generation...")
    sample_response = client.post("/wizard/image/sample", data={"target_size": "256"})
    assert sample_response.status_code == 200
    sample_data = sample_response.json()
    sample_id = sample_data["image_id"]
    
    # Verify sample image properties
    assert sample_data["face_detected"] is True
    assert sample_data["output_size"] == [256, 256]
    assert "files" in sample_data
    
    # Verify sample image is accessible
    face_response = client.get(f"/wizard/image/{sample_id}/face")
    assert face_response.status_code == 200
    assert face_response.headers["content-type"] == "image/png"
    
    original_response = client.get(f"/wizard/image/{sample_id}/original")
    assert original_response.status_code == 200
    assert original_response.headers["content-type"] == "image/png"
    
    # Test different sizes
    print("Testing different sample sizes...")
    for size in ["128", "512", "1024"]:
        size_response = client.post("/wizard/image/sample", data={"target_size": size})
        assert size_response.status_code == 200
        size_data = size_response.json()
        size_id = size_data["image_id"]
        
        assert size_data["output_size"] == [int(size), int(size)]
        
        # Clean up
        client.delete(f"/wizard/image/{size_id}")
    
    # Test invalid size
    print("Testing invalid sample size...")
    invalid_size_response = client.post("/wizard/image/sample", data={"target_size": "invalid"})
    assert invalid_size_response.status_code == 422
    
    # Clean up
    client.delete(f"/wizard/image/{sample_id}")
    
    print("Sample generation workflow test passed!")


def test_data_integrity_workflow(sample_text, sample_image):
    """Test data integrity throughout the workflow."""
    
    print("Testing data integrity workflow...")
    
    # Upload text
    text_response = client.post("/wizard/text/upload", data={"text": sample_text})
    assert text_response.status_code == 200
    text_data = text_response.json()
    text_id = text_data["text_id"]
    
    # Upload image
    with open(sample_image, 'rb') as f:
        image_response = client.post(
            "/wizard/image/upload",
            files={"file": ("test.png", f, "image/png")}
        )
    
    assert image_response.status_code == 200
    image_data = image_response.json()
    image_id = image_data["image_id"]
    
    try:
        # Verify text data integrity
        print("Verifying text data integrity...")
        for _ in range(5):
            # Get profile
            profile_response = client.get(f"/wizard/text/{text_id}/profile")
            assert profile_response.status_code == 200
            profile = profile_response.json()
            assert profile["text_id"] == text_id
            
            # Get raw text
            raw_response = client.get(f"/wizard/text/{text_id}/raw")
            assert raw_response.status_code == 200
            raw = raw_response.json()
            assert raw["text"] == sample_text
            assert raw["text_id"] == text_id
            
            time.sleep(0.1)
        
        # Verify image data integrity
        print("Verifying image data integrity...")
        for _ in range(5):
            # Get info
            info_response = client.get(f"/wizard/image/{image_id}/info")
            assert info_response.status_code == 200
            info = info_response.json()
            assert info["image_id"] == image_id
            
            # Get face image
            face_response = client.get(f"/wizard/image/{image_id}/face")
            assert face_response.status_code == 200
            assert len(face_response.content) > 0
            
            # Get original image
            original_response = client.get(f"/wizard/image/{image_id}/original")
            assert original_response.status_code == 200
            assert len(original_response.content) > 0
            
            time.sleep(0.1)
        
        # Verify data consistency
        print("Verifying data consistency...")
        profile1 = client.get(f"/wizard/text/{text_id}/profile").json()
        profile2 = client.get(f"/wizard/text/{text_id}/profile").json()
        assert profile1 == profile2
        
        info1 = client.get(f"/wizard/image/{image_id}/info").json()
        info2 = client.get(f"/wizard/image/{image_id}/info").json()
        assert info1 == info2
        
    finally:
        # Clean up
        client.delete(f"/wizard/text/{text_id}")
        client.delete(f"/wizard/image/{image_id}")
    
    print("Data integrity workflow test passed!")


def test_performance_workflow():
    """Test performance characteristics of the workflow."""
    
    print("Testing performance workflow...")
    
    import time
    
    # Test text upload performance
    print("Testing text upload performance...")
    text_content = "This is a performance test text. " * 100  # ~3000 characters
    
    start_time = time.time()
    text_response = client.post("/wizard/text/upload", data={"text": text_content})
    text_upload_time = time.time() - start_time
    
    assert text_response.status_code == 200
    text_id = text_response.json()["text_id"]
    
    print(f"Text upload time: {text_upload_time:.2f}s")
    assert text_upload_time < 5.0  # Should complete within 5 seconds
    
    # Test image upload performance
    print("Testing image upload performance...")
    img = Image.new('RGB', (500, 500), color='red')
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        img.save(f.name, 'PNG')
        temp_path = f.name
    
    try:
        start_time = time.time()
        with open(temp_path, 'rb') as f:
            image_response = client.post(
                "/wizard/image/upload",
                files={"file": ("test.png", f, "image/png")}
            )
        image_upload_time = time.time() - start_time
        
        assert image_response.status_code == 200
        image_id = image_response.json()["image_id"]
        
        print(f"Image upload time: {image_upload_time:.2f}s")
        assert image_upload_time < 10.0  # Should complete within 10 seconds
        
        # Test access performance
        print("Testing access performance...")
        
        # Text access
        start_time = time.time()
        profile_response = client.get(f"/wizard/text/{text_id}/profile")
        text_access_time = time.time() - start_time
        
        assert profile_response.status_code == 200
        print(f"Text access time: {text_access_time:.2f}s")
        assert text_access_time < 1.0  # Should complete within 1 second
        
        # Image access
        start_time = time.time()
        face_response = client.get(f"/wizard/image/{image_id}/face")
        image_access_time = time.time() - start_time
        
        assert face_response.status_code == 200
        print(f"Image access time: {image_access_time:.2f}s")
        assert image_access_time < 1.0  # Should complete within 1 second
        
        # Clean up
        client.delete(f"/wizard/image/{image_id}")
        
    finally:
        Path(temp_path).unlink()
    
    # Clean up
    client.delete(f"/wizard/text/{text_id}")
    
    print("Performance workflow test passed!")
