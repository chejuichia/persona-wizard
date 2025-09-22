"""
Foundry Local Integration Service

Provides integration with Foundry Local for model orchestration and inference.
"""

import asyncio
import json
import subprocess
import tempfile
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

from ...core.config import settings
from ...core.logging import get_logger

logger = get_logger(__name__)


class FoundryLocalClient:
    """Client for Foundry Local integration."""
    
    def __init__(self):
        """Initialize Foundry Local client."""
        self.is_available = False
        self.endpoint = "http://127.0.0.1:53224"  # Foundry Local endpoint
        self.models_dir = Path(settings.models_dir)
        
        # Check if Foundry Local is available
        self._check_availability()
    
    def _check_availability(self):
        """Check if Foundry Local is available."""
        try:
            import requests
            response = requests.get(f"{self.endpoint}/health", timeout=5)
            if response.status_code == 200:
                self.is_available = True
                logger.info("Foundry Local is available")
            else:
                logger.warning("Foundry Local endpoint not responding")
        except Exception as e:
            logger.warning(f"Foundry Local not available: {e}")
            self.is_available = False
    
    async def generate_text(
        self,
        prompt: str,
        model_name: str = "phi-3.5-mini",
        max_tokens: int = 256,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using Foundry Local.
        
        Args:
            prompt: Input prompt
            model_name: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            Dict with generated text and metadata
        """
        if not self.is_available:
            raise RuntimeError("Foundry Local is not available. Please start Foundry Local service.")
        
        return await self._generate_via_foundry(
            prompt, model_name, max_tokens, temperature, **kwargs
        )
    
    async def _generate_via_foundry(
        self,
        prompt: str,
        model_name: str,
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text via Foundry Local API."""
        try:
            import aiohttp
            
            # Prepare request payload
            payload = {
                "model": model_name,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": kwargs.get("top_p", 0.9),
                "stream": False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.endpoint}/v1/completions",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(f"Foundry Local API error {response.status}: {error_text}")
                    
                    result = await response.json()
                    
                    if "choices" not in result or not result["choices"]:
                        raise RuntimeError("Invalid response from Foundry Local API")
                    
                    generated_text = result["choices"][0]["text"]
                    
                    return {
                        "text": generated_text,
                        "word_count": len(generated_text.split()),
                        "char_count": len(generated_text),
                        "tokens_generated": result.get("usage", {}).get("completion_tokens", 0),
                        "model_name": model_name,
                        "temperature": temperature,
                        "via_foundry": True
                    }
                    
        except asyncio.TimeoutError:
            raise RuntimeError("Foundry Local request timed out after 60 seconds")
        except Exception as e:
            logger.error(f"Foundry Local generation failed: {e}")
            raise RuntimeError(f"Foundry Local generation failed: {e}")
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models from Foundry Local."""
        if not self.is_available:
            raise RuntimeError("Foundry Local is not available. Please start Foundry Local service.")
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.endpoint}/v1/models",
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(f"Foundry Local API error {response.status}: {error_text}")
                    
                    result = await response.json()
                    return result.get("data", [])
                    
        except Exception as e:
            logger.error(f"Failed to list models from Foundry Local: {e}")
            raise RuntimeError(f"Failed to list models: {e}")
    
    def start_service(self) -> bool:
        """Start Foundry Local service."""
        try:
            # Try to start Foundry Local service
            result = subprocess.run(
                ["foundry", "service", "start"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info("Foundry Local service started successfully")
                # Recheck availability
                self._check_availability()
                return self.is_available
            else:
                logger.error(f"Failed to start Foundry Local: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Foundry Local start command timed out")
            return False
        except FileNotFoundError:
            logger.error("Foundry Local not found. Please install it first.")
            return False
        except Exception as e:
            logger.error(f"Error starting Foundry Local: {e}")
            return False
    
    def stop_service(self) -> bool:
        """Stop Foundry Local service."""
        try:
            result = subprocess.run(
                ["foundry", "service", "stop"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info("Foundry Local service stopped successfully")
                self.is_available = False
                return True
            else:
                logger.error(f"Failed to stop Foundry Local: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error stopping Foundry Local: {e}")
            return False