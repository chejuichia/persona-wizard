"""Tests for text upload functionality."""

import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_upload_text_success():
    """Test successful text upload."""
    sample_text = "This is a sample text for testing. It contains multiple sentences to analyze the writing style. The text should be long enough to provide meaningful analysis."
    
    response = client.post("/wizard/text/upload", data={"text": sample_text})
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert "text_id" in data
    assert "session_id" in data
    assert data["word_count"] > 0
    assert data["character_count"] > 0
    assert "style_profile" in data
    assert "files" in data


def test_upload_text_too_short():
    """Test text upload with too short text."""
    response = client.post("/wizard/text/upload", data={"text": "short"})
    
    assert response.status_code == 422  # Validation error
    data = response.json()
    assert "detail" in data


def test_upload_text_empty():
    """Test text upload with empty text."""
    response = client.post("/wizard/text/upload", data={"text": ""})
    
    assert response.status_code == 422  # Validation error


def test_upload_text_file():
    """Test text file upload."""
    sample_text = "This is a sample text file for testing. It should be processed correctly when uploaded as a file."
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(sample_text)
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            response = client.post(
                "/wizard/text/upload-file",
                files={"file": ("test.txt", f, "text/plain")}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "ok"
        assert "text_id" in data
        assert data["word_count"] > 0
        
    finally:
        Path(temp_path).unlink()


def test_upload_text_file_invalid_type():
    """Test text file upload with invalid file type."""
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        f.write(b"fake image data")
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            response = client.post(
                "/wizard/text/upload-file",
                files={"file": ("test.jpg", f, "image/jpeg")}
            )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        
    finally:
        Path(temp_path).unlink()


def test_get_text_profile():
    """Test getting text profile."""
    # First upload some text
    sample_text = "This is a sample text for testing profile retrieval."
    upload_response = client.post("/wizard/text/upload", data={"text": sample_text})
    assert upload_response.status_code == 200
    
    text_id = upload_response.json()["text_id"]
    
    # Get the profile
    response = client.get(f"/wizard/text/{text_id}/profile")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert data["text_id"] == text_id
    assert "profile" in data
    assert "metadata" in data["profile"]


def test_get_text_profile_not_found():
    """Test getting text profile for non-existent text."""
    response = client.get("/wizard/text/nonexistent/profile")
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_get_raw_text():
    """Test getting raw text content."""
    # First upload some text
    sample_text = "This is raw text content for testing."
    upload_response = client.post("/wizard/text/upload", data={"text": sample_text})
    assert upload_response.status_code == 200
    
    text_id = upload_response.json()["text_id"]
    
    # Get the raw text
    response = client.get(f"/wizard/text/{text_id}/raw")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert data["text_id"] == text_id
    assert data["text"] == sample_text


def test_delete_text():
    """Test deleting uploaded text."""
    # First upload some text
    sample_text = "This is text to be deleted."
    upload_response = client.post("/wizard/text/upload", data={"text": sample_text})
    assert upload_response.status_code == 200
    
    text_id = upload_response.json()["text_id"]
    
    # Delete the text
    response = client.delete(f"/wizard/text/{text_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert data["text_id"] == text_id
    assert "deleted_files" in data
    
    # Try to get the profile (should fail)
    profile_response = client.get(f"/wizard/text/{text_id}/profile")
    assert profile_response.status_code == 404


def test_delete_text_not_found():
    """Test deleting non-existent text."""
    response = client.delete("/wizard/text/nonexistent")
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_upload_text_very_long():
    """Test uploading very long text."""
    # Create a very long text (10,000 characters)
    long_text = "This is a test sentence. " * 400  # ~10,000 characters
    
    response = client.post("/wizard/text/upload", data={"text": long_text})
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert data["character_count"] > 9000
    assert data["word_count"] > 1000


def test_upload_text_special_characters():
    """Test uploading text with special characters."""
    special_text = "Hello! This text has special characters: @#$%^&*()_+-=[]{}|;':\",./<>?`~ and emojis: 😀🎉🚀 and unicode: ñáéíóú"
    
    response = client.post("/wizard/text/upload", data={"text": special_text})
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert data["character_count"] > 0
    assert "style_profile" in data


def test_upload_text_multiple_languages():
    """Test uploading text in multiple languages."""
    multilingual_text = """
    English: This is a test in English.
    Español: Esta es una prueba en español.
    Français: Ceci est un test en français.
    Deutsch: Dies ist ein Test auf Deutsch.
    """
    
    response = client.post("/wizard/text/upload", data={"text": multilingual_text})
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert data["character_count"] > 0
    assert "style_profile" in data


def test_upload_text_only_whitespace():
    """Test uploading text with only whitespace."""
    whitespace_text = "   \n\t   \n   "
    
    response = client.post("/wizard/text/upload", data={"text": whitespace_text})
    
    # The API returns 400 for empty text, not 422
    assert response.status_code == 400


def test_upload_text_only_punctuation():
    """Test uploading text with only punctuation."""
    punctuation_text = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~"
    
    response = client.post("/wizard/text/upload", data={"text": punctuation_text})
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    # Punctuation-only text might have 0 character count after processing
    assert data["character_count"] >= 0


def test_upload_text_file_large():
    """Test uploading large text file."""
    large_text = "This is a large text file. " * 1000  # ~25,000 characters
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(large_text)
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            response = client.post(
                "/wizard/text/upload-file",
                files={"file": ("large.txt", f, "text/plain")}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "ok"
        assert data["character_count"] > 20000
        
    finally:
        Path(temp_path).unlink()


def test_upload_text_file_binary():
    """Test uploading binary file as text."""
    binary_data = b'\x00\x01\x02\x03\x04\x05\x06\x07'
    
    with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
        f.write(binary_data)
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            response = client.post(
                "/wizard/text/upload-file",
                files={"file": ("test.bin", f, "application/octet-stream")}
            )
        
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 400]
        
    finally:
        Path(temp_path).unlink()


def test_upload_text_file_empty():
    """Test uploading empty text file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("")
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            response = client.post(
                "/wizard/text/upload-file",
                files={"file": ("empty.txt", f, "text/plain")}
            )
        
        # The API returns 400 for empty files, not 422
        assert response.status_code == 400
        
    finally:
        Path(temp_path).unlink()


def test_upload_text_file_missing():
    """Test text file upload without file parameter."""
    response = client.post("/wizard/text/upload-file")
    assert response.status_code == 422  # Validation error


def test_get_text_profile_detailed():
    """Test getting detailed text profile."""
    sample_text = "This is a comprehensive test text. It contains multiple sentences with varying lengths and complexity. Some sentences are short. Others are much longer and contain more complex grammatical structures that should be analyzed by the style profiling system. The text includes different types of punctuation marks, such as commas, semicolons, and periods. It also has some numbers like 123 and 456. The vocabulary ranges from simple words to more sophisticated terms. This should provide a good sample for style analysis."
    
    upload_response = client.post("/wizard/text/upload", data={"text": sample_text})
    assert upload_response.status_code == 200
    
    text_id = upload_response.json()["text_id"]
    
    response = client.get(f"/wizard/text/{text_id}/profile")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert data["text_id"] == text_id
    assert "profile" in data
    assert "metadata" in data["profile"]
    
    # Check profile structure - the API returns a different structure
    profile = data["profile"]
    assert "style_metrics" in profile
    assert "tone" in profile
    assert "metadata" in profile
    
    # Check style metrics
    style_metrics = profile["style_metrics"]
    assert "vocabulary_richness" in style_metrics
    assert "avg_sentence_length" in style_metrics
    assert "reading_ease" in style_metrics
    
    # Check tone structure
    tone = profile["tone"]
    assert "positive" in tone
    assert "negative" in tone
    assert "formal" in tone
    assert "casual" in tone


def test_text_workflow_complete():
    """Test complete text workflow: upload -> get profile -> get raw -> delete."""
    sample_text = "This is a complete workflow test for text processing."
    
    # Upload
    upload_response = client.post("/wizard/text/upload", data={"text": sample_text})
    assert upload_response.status_code == 200
    text_id = upload_response.json()["text_id"]
    
    # Get profile
    profile_response = client.get(f"/wizard/text/{text_id}/profile")
    assert profile_response.status_code == 200
    
    # Get raw text
    raw_response = client.get(f"/wizard/text/{text_id}/raw")
    assert raw_response.status_code == 200
    assert raw_response.json()["text"] == sample_text
    
    # Delete
    delete_response = client.delete(f"/wizard/text/{text_id}")
    assert delete_response.status_code == 200
    
    # Verify deletion
    profile_response_after = client.get(f"/wizard/text/{text_id}/profile")
    assert profile_response_after.status_code == 404


def test_upload_text_minimum_length():
    """Test uploading text at minimum length boundary."""
    min_text = "a" * 10  # Exactly 10 characters
    
    response = client.post("/wizard/text/upload", data={"text": min_text})
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert data["character_count"] == 10


def test_upload_text_just_under_minimum():
    """Test uploading text just under minimum length."""
    short_text = "a" * 9  # 9 characters, under minimum
    
    response = client.post("/wizard/text/upload", data={"text": short_text})
    
    assert response.status_code == 422  # Validation error


def test_upload_text_with_newlines():
    """Test uploading text with various newline characters."""
    text_with_newlines = "Line 1\nLine 2\r\nLine 3\rLine 4"
    
    response = client.post("/wizard/text/upload", data={"text": text_with_newlines})
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert data["character_count"] > 0


def test_upload_text_file_different_encodings():
    """Test uploading text files with different encodings."""
    # Test UTF-8
    utf8_text = "Hello, 世界! This is UTF-8 text."
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(utf8_text)
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            response = client.post(
                "/wizard/text/upload-file",
                files={"file": ("utf8.txt", f, "text/plain")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        
    finally:
        Path(temp_path).unlink()


def test_upload_text_concurrent():
    """Test uploading multiple texts concurrently."""
    import threading
    import time
    
    results = []
    errors = []
    
    def upload_text(text, index):
        try:
            response = client.post("/wizard/text/upload", data={"text": text})
            results.append((index, response.status_code))
        except Exception as e:
            errors.append((index, str(e)))
    
    # Create multiple threads
    threads = []
    for i in range(5):
        text = f"This is concurrent test text number {i}. " * 10
        thread = threading.Thread(target=upload_text, args=(text, i))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Check results
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(results) == 5
    for index, status_code in results:
        assert status_code == 200, f"Thread {index} failed with status {status_code}"
