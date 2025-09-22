"""
Tests for bundle building functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.services.bundle.builder import BundleBuilder

client = TestClient(app)


class TestBundleBuilder:
    """Test the BundleBuilder service."""
    
    def test_build_persona_bundle_minimal(self):
        """Test building a minimal persona bundle."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a temporary data directory
            data_dir = Path(temp_dir) / "data"
            data_dir.mkdir()
            
            # Create artifacts directory structure
            artifacts_dir = data_dir / "artifacts"
            artifacts_dir.mkdir()
            (artifacts_dir / "text").mkdir()
            (artifacts_dir / "image").mkdir()
            (artifacts_dir / "voice").mkdir()
            
            # Create personas directory
            personas_dir = data_dir / "personas"
            personas_dir.mkdir()
            
            # Create outputs directory
            outputs_dir = data_dir / "outputs"
            outputs_dir.mkdir()
            
            # Mock the settings to use our temp directory
            import app.services.bundle.builder as builder_module
            original_data_dir = builder_module.settings.data_dir
            builder_module.settings.data_dir = data_dir
            
            try:
                builder = BundleBuilder()
                
                # Build a minimal persona bundle
                result = builder.build_persona_bundle(
                    persona_id="test-persona-123",
                    name="Test Persona"
                )
                
                # Verify the result
                assert result["persona_id"] == "test-persona-123"
                assert "bundle_path" in result
                assert "manifest_path" in result
                assert "artifacts_copied" in result
                assert "size_bytes" in result
                
                # Verify the bundle file exists
                bundle_path = Path(result["bundle_path"])
                assert bundle_path.exists()
                assert bundle_path.suffix == ".zip"
                
                # Verify the manifest exists
                manifest_path = Path(result["manifest_path"])
                assert manifest_path.exists()
                
                # Verify the persona directory structure
                persona_dir = personas_dir / "test-persona-123"
                assert persona_dir.exists()
                assert (persona_dir / "persona.yaml").exists()
                assert (persona_dir / "run_local_inference.py").exists()
                assert (persona_dir / "configs").exists()
                assert (persona_dir / "artifacts").exists()
                
            finally:
                # Restore original settings
                builder_module.settings.data_dir = original_data_dir
    
    def test_build_persona_bundle_with_artifacts(self):
        """Test building a persona bundle with text and image artifacts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a temporary data directory
            data_dir = Path(temp_dir) / "data"
            data_dir.mkdir()
            
            # Create artifacts directory structure
            artifacts_dir = data_dir / "artifacts"
            artifacts_dir.mkdir()
            (artifacts_dir / "text").mkdir()
            (artifacts_dir / "image").mkdir()
            (artifacts_dir / "voice").mkdir()
            
            # Create personas directory
            personas_dir = data_dir / "personas"
            personas_dir.mkdir()
            
            # Create outputs directory
            outputs_dir = data_dir / "outputs"
            outputs_dir.mkdir()
            
            # Create some test artifacts
            text_id = "test-text-123"
            image_id = "test-image-456"
            
            # Create text artifacts
            style_profile = {
                "vocabulary_richness": 0.8,
                "avg_sentence_length": 15.5,
                "reading_ease": 0.7,
                "tone": {"formal": 0.3, "casual": 0.7}
            }
            
            import json
            with open(artifacts_dir / "text" / f"{text_id}_style_profile.json", 'w') as f:
                json.dump(style_profile, f)
            
            with open(artifacts_dir / "text" / f"{text_id}_raw.txt", 'w') as f:
                f.write("This is a test text sample for style analysis.")
            
            # Create image artifacts (dummy file)
            with open(artifacts_dir / "image" / f"{image_id}_face_ref.png", 'w') as f:
                f.write("dummy image data")
            
            # Mock the settings to use our temp directory
            import app.services.bundle.builder as builder_module
            original_data_dir = builder_module.settings.data_dir
            builder_module.settings.data_dir = data_dir
            
            try:
                builder = BundleBuilder()
                
                # Build a persona bundle with artifacts
                result = builder.build_persona_bundle(
                    persona_id="test-persona-with-artifacts",
                    text_id=text_id,
                    image_id=image_id,
                    name="Test Persona with Artifacts"
                )
                
                # Verify the result
                assert result["persona_id"] == "test-persona-with-artifacts"
                assert "style_profile" in result["artifacts_copied"]
                assert "face_ref" in result["artifacts_copied"]
                
                # Verify artifacts were copied
                persona_dir = personas_dir / "test-persona-with-artifacts"
                assert (persona_dir / "artifacts" / "text" / "style_profile.json").exists()
                assert (persona_dir / "artifacts" / "text" / "raw.txt").exists()
                assert (persona_dir / "artifacts" / "image" / "face_ref.png").exists()
                
            finally:
                # Restore original settings
                builder_module.settings.data_dir = original_data_dir
    
    def test_get_bundle_info(self):
        """Test getting bundle information."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a temporary data directory
            data_dir = Path(temp_dir) / "data"
            data_dir.mkdir()
            
            # Create personas directory
            personas_dir = data_dir / "personas"
            personas_dir.mkdir()
            
            # Create outputs directory
            outputs_dir = data_dir / "outputs"
            outputs_dir.mkdir()
            
            # Create a dummy bundle file
            bundle_path = outputs_dir / "persona_test-123.zip"
            with open(bundle_path, 'w') as f:
                f.write("dummy bundle content")
            
            # Mock the settings to use our temp directory
            import app.services.bundle.builder as builder_module
            original_data_dir = builder_module.settings.data_dir
            builder_module.settings.data_dir = data_dir
            
            try:
                builder = BundleBuilder()
                
                # Test getting bundle info
                info = builder.get_bundle_info("test-123")
                assert info is not None
                assert info["persona_id"] == "test-123"
                assert info["bundle_path"] == str(bundle_path)
                assert info["size_bytes"] > 0
                
                # Test getting info for non-existent bundle
                info = builder.get_bundle_info("non-existent")
                assert info is None
                
            finally:
                # Restore original settings
                builder_module.settings.data_dir = original_data_dir


class TestBundleEndpoints:
    """Test the bundle API endpoints."""
    
    def test_build_persona_endpoint(self):
        """Test the build persona endpoint."""
        response = client.post("/wizard/build/", json={
            "name": "Test Persona",
            "text_id": None,
            "image_id": None,
            "voice_id": None
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "persona_id" in data
        assert "bundle_path" in data
        assert "artifacts_copied" in data
        assert "size_bytes" in data
    
    def test_build_persona_with_artifacts(self):
        """Test building persona with artifacts."""
        response = client.post("/wizard/build/", json={
            "name": "Test Persona with Artifacts",
            "text_id": "test-text-123",
            "image_id": "test-image-456",
            "voice_id": "test-voice-789"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "persona_id" in data
    
    def test_download_bundle_endpoint(self):
        """Test the download bundle endpoint."""
        # First build a persona
        build_response = client.post("/wizard/build/", json={
            "name": "Download Test Persona"
        })
        assert build_response.status_code == 200
        
        persona_id = build_response.json()["persona_id"]
        
        # Then try to download it
        response = client.get(f"/wizard/build/{persona_id}/download")
        
        # Should return 200 since the bundle file is actually created
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
    
    def test_get_bundle_info_endpoint(self):
        """Test the get bundle info endpoint."""
        # First build a persona
        build_response = client.post("/wizard/build/", json={
            "name": "Info Test Persona"
        })
        assert build_response.status_code == 200
        
        persona_id = build_response.json()["persona_id"]
        
        # Then try to get info
        response = client.get(f"/wizard/build/{persona_id}/info")
        
        # Should return 200 since the bundle file is actually created
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["persona_id"] == persona_id
        assert "bundle_path" in data
        assert "size_bytes" in data
    
    def test_download_nonexistent_bundle(self):
        """Test downloading a non-existent bundle."""
        response = client.get("/wizard/build/non-existent-id/download")
        assert response.status_code == 404
    
    def test_get_info_nonexistent_bundle(self):
        """Test getting info for a non-existent bundle."""
        response = client.get("/wizard/build/non-existent-id/info")
        assert response.status_code == 404
