"""Tests for health endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    
    data = response.json()
    assert data["ok"] is True
    assert "timestamp" in data
    assert "version" in data


def test_readiness_check():
    """Test readiness check endpoint."""
    response = client.get("/readyz")
    assert response.status_code == 200
    
    data = response.json()
    assert data["ready"] is True
    assert "device" in data
    assert "memory" in data
    assert "timestamp" in data


def test_device_info():
    """Test device info endpoint."""
    response = client.get("/device")
    assert response.status_code == 200
    
    data = response.json()
    assert "device" in data
    assert "memory" in data
    assert "timestamp" in data


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == "Persona Wizard API"
    assert data["version"] == "0.1.0"
    assert data["docs"] == "/docs"
    assert data["health"] == "/healthz"
