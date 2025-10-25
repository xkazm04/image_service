"""
Prompt validation and optimization service for image generation
Handles prompt length validation, optimization using Ollama, and error management
"""

import logging
import time
from typing import Dict, Any, Optional, Tuple
from enum import Enum

from ..ollama import OllamaClient, OllamaConfig, OllamaRequest, OllamaResponse
from ...prompts.prompt_templates import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

class PromptValidationResult(Enum):
    """Result types for prompt validation"""
    VALID = "valid"
    OPTIMIZED = "optimized"
    TOO_LONG = "too_long"
    OPTIMIZATION_FAILED = "optimization_failed"

class PromptValidationError(Exception):
    """Custom exception for prompt validation errors"""
    pass

class PromptValidationResponse:
    """Response object for prompt validation operations"""
    
    def __init__(
        self,
        result: PromptValidationResult,
        original_prompt: str,
        optimized_prompt: Optional[str] = None,
        original_length: int = 0,
        optimized_length: int = 0,
        optimization_time: Optional[float] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.result = result
        self.original_prompt = original_prompt
        self.optimized_prompt = optimized_prompt or original_prompt
        self.original_length = original_length
        self.optimized_length = optimized_length
        self.optimization_time = optimization_time
        self.error_message = error_message
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "result": self.result.value,
            "original_prompt": self.original_prompt,
            "optimized_prompt": self.optimized_prompt,
            "original_length": self.original_length,
            "optimized_length": self.optimized_length,
            "optimization_time": self.optimization_time,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "size_reduction": self.original_length - self.optimized_length if self.optimized_length else 0,
            "reduction_percentage": round(((self.original_length - self.optimized_length) / self.original_length) * 100, 2) if self.original_length > 0 and self.optimized_length else 0
        }

class PromptValidator:
    """Service for validating and optimizing image generation prompts"""
    
    # Configuration constants
    MAX_PROMPT_LENGTH = 10000
    OPTIMIZATION_THRESHOLD = 3000
    TARGET_LENGTH = 2800  # Leave some buffer under 3000
    
    def __init__(self, ollama_config: Optional[OllamaConfig] = None):
        """Initialize prompt validator with Ollama client"""
        self.ollama_config = ollama_config or OllamaConfig(
            base_url="http://localhost:11434",
            default_model="gpt-oss:20b",
            timeout=120,  # 2 minutes for prompt optimization
            max_retries=2
        )
        self.ollama_client = OllamaClient(self.ollama_config)
        
    async def validate_and_optimize(
        self, 
        prompt: str, 
        force_optimize: bool = False
    ) -> PromptValidationResponse:
        """
        Validate prompt length and optimize if necessary
        
        Args:
            prompt: The input prompt to validate
            force_optimize: Force optimization even if under threshold
            
        Returns:
            PromptValidationResponse with validation results
        """
        
        start_time = time.time()
        original_length = len(prompt)
        
        logger.info(f"Validating prompt of length {original_length}")
        
        # Check if prompt exceeds maximum length
        if original_length > self.MAX_PROMPT_LENGTH:
            logger.warning(f"Prompt too long: {original_length} > {self.MAX_PROMPT_LENGTH}")
            return PromptValidationResponse(
                result=PromptValidationResult.TOO_LONG,
                original_prompt=prompt,
                original_length=original_length,
                error_message=f"Prompt exceeds maximum length of {self.MAX_PROMPT_LENGTH} characters"
            )
        
        # Check if optimization is needed
        needs_optimization = original_length > self.OPTIMIZATION_THRESHOLD or force_optimize
        
        if not needs_optimization:
            logger.info(f"Prompt is within acceptable length: {original_length} <= {self.OPTIMIZATION_THRESHOLD}")
            return PromptValidationResponse(
                result=PromptValidationResult.VALID,
                original_prompt=prompt,
                original_length=original_length,
                optimized_length=original_length
            )
        
        # Perform optimization
        logger.info(f"Optimizing prompt from {original_length} characters")
        
        try:
            optimization_result = await self._optimize_prompt(prompt)
            optimization_time = time.time() - start_time
            
            if optimization_result.success and optimization_result.response:
                optimized_prompt = optimization_result.response.strip()
                optimized_length = len(optimized_prompt)
                
                logger.info(f"Optimization successful: {original_length} → {optimized_length} characters ({optimization_time:.2f}s)")
                
                return PromptValidationResponse(
                    result=PromptValidationResult.OPTIMIZED,
                    original_prompt=prompt,
                    optimized_prompt=optimized_prompt,
                    original_length=original_length,
                    optimized_length=optimized_length,
                    optimization_time=optimization_time,
                    metadata={
                        "ollama_model": optimization_result.model,
                        "ollama_tokens": optimization_result.eval_count,
                        "ollama_duration": optimization_result.total_duration
                    }
                )
            else:
                error_msg = optimization_result.error or "Unknown optimization error"
                logger.error(f"Optimization failed: {error_msg}")
                
                return PromptValidationResponse(
                    result=PromptValidationResult.OPTIMIZATION_FAILED,
                    original_prompt=prompt,
                    original_length=original_length,
                    optimization_time=time.time() - start_time,
                    error_message=f"Prompt optimization failed: {error_msg}"
                )
                
        except Exception as e:
            error_msg = f"Unexpected error during optimization: {str(e)}"
            logger.error(error_msg)
            
            return PromptValidationResponse(
                result=PromptValidationResult.OPTIMIZATION_FAILED,
                original_prompt=prompt,
                original_length=original_length,
                optimization_time=time.time() - start_time,
                error_message=error_msg
            )
    
    async def _optimize_prompt(self, prompt: str) -> OllamaResponse:
        """Use Ollama to optimize the prompt"""
        
        # Prepare optimization request
        user_prompt = USER_PROMPT_TEMPLATE.format(original_prompt=prompt)
        
        ollama_request = OllamaRequest(
            prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.3,  # Lower temperature for more consistent optimization
            max_tokens=1000   # Reasonable limit for optimized prompt
        )
        
        # Generate optimized prompt
        return await self.ollama_client.generate(ollama_request)
    
    async def check_ollama_availability(self) -> bool:
        """Check if Ollama service is available"""
        return await self.ollama_client.check_availability()
    
    async def get_optimization_stats(self, prompt: str) -> Dict[str, Any]:
        """Get analysis stats for a prompt without optimization"""
        length = len(prompt)
        words = len(prompt.split())
        
        return {
            "character_count": length,
            "word_count": words,
            "needs_optimization": length > self.OPTIMIZATION_THRESHOLD,
            "exceeds_maximum": length > self.MAX_PROMPT_LENGTH,
            "optimization_threshold": self.OPTIMIZATION_THRESHOLD,
            "maximum_length": self.MAX_PROMPT_LENGTH,
            "estimated_reduction_needed": max(0, length - self.TARGET_LENGTH)
        }
    
    async def close(self):
        """Close Ollama client connection"""
        await self.ollama_client.close()

# Global validator instance
_global_validator = None

def get_prompt_validator(ollama_config: Optional[OllamaConfig] = None) -> PromptValidator:
    """Get global prompt validator instance"""
    global _global_validator
    if _global_validator is None:
        _global_validator = PromptValidator(ollama_config)
    return _global_validator

async def close_global_validator():
    """Close global validator"""
    global _global_validator
    if _global_validator:
        await _global_validator.close()
        _global_validator = None