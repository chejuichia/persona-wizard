"""
Text Generation Service

Implements local LLM text generation with persona style adaptation.
Uses small, Foundry-Local-compatible models for local inference.
"""

import asyncio
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

try:
    import torch
    import transformers
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from ...core.config import settings
from ...core.logging import get_logger
from ...services.foundry.local_client import FoundryLocalClient

logger = get_logger(__name__)


class TextGenerator:
    """Local LLM text generation with persona style adaptation."""
    
    def __init__(self, model_name: str = None, device: str = "auto"):
        """
        Initialize text generator.
        
        Args:
            model_name: Hugging Face model name (defaults to phi-4-mini)
            device: Device to run on ("cpu", "cuda", "auto")
        """
        self.model_name = model_name or settings.default_llm_model
        self.device = self._get_device(device)
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.is_initialized = False
        
        # Generation parameters
        self.max_new_tokens = 256
        self.temperature = 0.7
        self.top_p = 0.9
        self.do_sample = True
        
        # Models directory
        self.models_dir = Path(settings.models_dir) / "llm"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Foundry Local client
        self.foundry_client = FoundryLocalClient()
        
        logger.info(f"Initializing TextGenerator with model: {model_name}")
    
    def _get_device(self, device: str) -> str:
        """Determine the best available device."""
        if device == "auto":
            if TORCH_AVAILABLE and torch.cuda.is_available():
                return "cuda"
            return "cpu"
        return device
    
    async def _load_model(self):
        """Load the LLM model and tokenizer."""
        if self.is_initialized:
            return
        
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available, using mock implementation")
            self.is_initialized = True
            return
        
        try:
            logger.info(f"Loading LLM model: {self.model_name}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=str(self.models_dir)
            )
            
            # Add padding token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                cache_dir=str(self.models_dir),
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None
            )
            
            # Move to device if not using device_map
            if self.device == "cpu":
                self.model = self.model.to(self.device)
            
            # Create pipeline
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
            
            self.is_initialized = True
            logger.info("LLM model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load LLM model: {e}")
            # Fall back to mock implementation
            self.is_initialized = True
            logger.info("Using mock LLM implementation")
    
    async def generate_text(
        self,
        prompt: str,
        style_profile: Optional[Dict[str, Any]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate text based on prompt and style profile.
        
        Args:
            prompt: Input prompt for text generation
            style_profile: Persona style profile from text analysis
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Dict with generated text and metadata
        """
        try:
            # Use provided parameters or defaults
            max_tokens = max_tokens or self.max_new_tokens
            temperature = temperature or self.temperature
            
            # Apply style adaptation if profile provided
            adapted_prompt = self._adapt_prompt_to_style(prompt, style_profile)
            
            # Use Foundry Local client for real model inference
            result = await self.foundry_client.generate_text(
                prompt=adapted_prompt,
                model_name=self.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=self.top_p,
                do_sample=self.do_sample
            )
            
            # Add style adaptation info
            result["style_adapted"] = style_profile is not None
            result["original_prompt"] = prompt
            result["adapted_prompt"] = adapted_prompt
            
            return result
            
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return await self._mock_generate_text(prompt, max_tokens or self.max_new_tokens)
    
    def _adapt_prompt_to_style(self, prompt: str, style_profile: Optional[Dict[str, Any]]) -> str:
        """Adapt prompt based on style profile."""
        if not style_profile:
            return prompt
        
        # Extract style characteristics
        style_metrics = style_profile.get("style_metrics", {})
        tone = style_profile.get("tone", {})
        
        # Build style context
        style_context = []
        
        # Add vocabulary richness info
        if "vocabulary_richness" in style_metrics:
            richness = style_metrics["vocabulary_richness"]
            if richness > 0.7:
                style_context.append("Use sophisticated vocabulary")
            elif richness < 0.3:
                style_context.append("Use simple, accessible language")
        
        # Add sentence length preference
        if "avg_sentence_length" in style_metrics:
            avg_length = style_metrics["avg_sentence_length"]
            if avg_length > 20:
                style_context.append("Use longer, more complex sentences")
            elif avg_length < 10:
                style_context.append("Use shorter, concise sentences")
        
        # Add tone guidance
        if "primary_tone" in tone:
            primary_tone = tone["primary_tone"]
            style_context.append(f"Maintain a {primary_tone} tone")
        
        # Combine with original prompt
        if style_context:
            style_instruction = " ".join(style_context)
            return f"{style_instruction}. {prompt}"
        
        return prompt
    
    async def _mock_generate_text(self, prompt: str, max_tokens: int) -> Dict[str, Any]:
        """Mock text generation for testing."""
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        # Generate mock responses based on prompt
        mock_responses = [
            f"I understand you're asking about {prompt.lower()}. Let me share my thoughts on this topic.",
            f"That's an interesting question about {prompt.lower()}. Here's what I think:",
            f"Regarding {prompt.lower()}, I believe the key points are:",
            f"When it comes to {prompt.lower()}, my perspective is:",
            f"I'd be happy to discuss {prompt.lower()} with you. Here's my take:"
        ]
        
        # Select response based on prompt length
        response_index = len(prompt) % len(mock_responses)
        base_response = mock_responses[response_index]
        
        # Add some variation
        variations = [
            " This is a complex topic that requires careful consideration.",
            " There are multiple factors to consider here.",
            " I think this deserves thoughtful analysis.",
            " This is something I've thought about quite a bit.",
            " Let me break this down for you."
        ]
        
        variation = variations[len(prompt) % len(variations)]
        generated_text = base_response + variation
        
        # Ensure we don't exceed max_tokens (rough approximation)
        words = generated_text.split()
        if len(words) > max_tokens // 2:  # Rough word-to-token ratio
            generated_text = " ".join(words[:max_tokens // 2])
        
        return {
            "text": generated_text,
            "word_count": len(generated_text.split()),
            "char_count": len(generated_text),
            "tokens_generated": len(generated_text.split()) * 1.3,  # Rough estimate
            "model_name": f"mock-{self.model_name}",
            "temperature": self.temperature,
            "style_adapted": False
        }
    
    async def generate_with_persona(
        self,
        prompt: str,
        persona_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate text using full persona configuration.
        
        Args:
            prompt: Input prompt
            persona_config: Complete persona configuration
            
        Returns:
            Dict with generated text and metadata
        """
        # Extract text configuration
        text_config = persona_config.get("text", {})
        generation_config = text_config.get("generation", {})
        
        # Get style profile if available
        style_profile = text_config.get("style_profile")
        
        # Use persona-specific parameters
        max_tokens = generation_config.get("max_new_tokens", self.max_new_tokens)
        temperature = generation_config.get("temperature", self.temperature)
        
        return await self.generate_text(
            prompt=prompt,
            style_profile=style_profile,
            max_tokens=max_tokens,
            temperature=temperature
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "is_initialized": self.is_initialized,
            "torch_available": TORCH_AVAILABLE,
            "max_new_tokens": self.max_new_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p
        }
    
    async def cleanup(self):
        """Clean up resources."""
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.is_initialized = False
        logger.info("TextGenerator cleaned up")


class MockTextGenerator(TextGenerator):
    """Mock text generator for testing."""
    
    def __init__(self, model_name: str = "mock-llm", device: str = "cpu"):
        super().__init__(model_name, device)
        self.is_initialized = True
        logger.info("Using mock TextGenerator implementation")
    
    async def _load_model(self):
        """Mock model loading."""
        self.is_initialized = True
    
    async def generate_text(
        self,
        prompt: str,
        style_profile: Optional[Dict[str, Any]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """Mock text generation with more realistic behavior."""
        await asyncio.sleep(0.2)  # Simulate processing time
        
        # Generate more sophisticated mock responses
        responses = [
            f"Based on your question about '{prompt}', I think it's important to consider multiple perspectives. This topic touches on several key areas that deserve careful analysis.",
            f"Regarding '{prompt}', my experience suggests that the most effective approach involves understanding the underlying principles. Let me share some insights that might be helpful.",
            f"When discussing '{prompt}', I find it valuable to examine both the theoretical framework and practical applications. Here's what I've learned from my research and experience.",
            f"Your question about '{prompt}' is quite thought-provoking. I believe the answer lies in understanding the interconnected nature of these concepts and their real-world implications.",
            f"Concerning '{prompt}', I'd like to offer a nuanced perspective that considers both the immediate context and the broader implications. This is a topic that requires careful consideration."
        ]
        
        # Select response based on prompt characteristics
        response_index = hash(prompt) % len(responses)
        base_response = responses[response_index]
        
        # Add style-adapted content if profile provided
        if style_profile:
            style_metrics = style_profile.get("style_metrics", {})
            tone = style_profile.get("tone", {})
            
            # Add style-specific elements
            if style_metrics.get("vocabulary_richness", 0.5) > 0.7:
                base_response += " The complexity of this subject matter demands sophisticated analysis and careful consideration of multiple variables."
            elif style_metrics.get("vocabulary_richness", 0.5) < 0.3:
                base_response += " Let me explain this in simple terms that are easy to understand."
            
            if tone.get("primary_tone") == "formal":
                base_response += " I trust this information will be of assistance to you."
            elif tone.get("primary_tone") == "casual":
                base_response += " Hope this helps! Let me know if you have any other questions."
        
        # Truncate if too long
        max_tokens = max_tokens or self.max_new_tokens
        words = base_response.split()
        if len(words) > max_tokens // 2:
            base_response = " ".join(words[:max_tokens // 2])
        
        return {
            "text": base_response,
            "word_count": len(base_response.split()),
            "char_count": len(base_response),
            "tokens_generated": len(base_response.split()) * 1.3,
            "model_name": f"mock-{self.model_name}",
            "temperature": temperature or self.temperature,
            "style_adapted": style_profile is not None
        }
