"""
Unified Image Generation Service
Aggregates multiple providers with automatic fallback and load balancing
Includes prompt validation and optimization
"""

import logging
import uuid
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from services.interfaces import (
    UniversalImageRequest, UniversalImageResponse, Provider, 
    GenerationStatus, ImageGenerationError, ProviderNotAvailableError
)
from services.providers import get_available_providers, create_provider, get_provider_configs
from services.prompt_validation import (
    PromptValidator, PromptValidationResult, PromptValidationResponse,
    get_prompt_validator, PromptValidationError
)
from models.models import GenerationJob
from database import get_db
from utils.storage import LocalStorage

logger = logging.getLogger(__name__)

class UnifiedImageService:
    """Unified service for image generation across multiple providers with prompt validation"""
    
    def __init__(self):
        self.providers = {}
        self.provider_configs = {}
        self.storage = LocalStorage()
        self.prompt_validator = get_prompt_validator()
        
        # Initialize available providers
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all available providers"""
        available_providers = get_available_providers()
        configs = get_provider_configs()
        
        for config in configs:
            if config and config.is_enabled:
                try:
                    provider_instance = create_provider(config.provider)
                    self.providers[config.provider] = provider_instance
                    self.provider_configs[config.provider] = config
                    logger.info(f"Initialized provider: {config.name}")
                except Exception as e:
                    logger.warning(f"Failed to initialize provider {config.provider}: {e}")
    
    def get_available_providers(self) -> List[Provider]:
        """Get list of available and working providers"""
        return list(self.providers.keys())
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers"""
        status = {}
        
        for provider_key, provider_instance in self.providers.items():
            try:
                config = self.provider_configs[provider_key]
                status[provider_key.value] = {
                    "name": config.name,
                    "available": True,
                    "description": config.description,
                    "max_images": config.max_images,
                    "supported_formats": config.supported_formats,
                    "supports_negative_prompt": config.supports_negative_prompt,
                    "supports_seed": config.supports_seed
                }
            except Exception as e:
                status[provider_key.value] = {
                    "available": False,
                    "error": str(e)
                }
        
        return status
    
    def select_provider(self, request: UniversalImageRequest) -> Provider:
        """Select the best provider for the request"""
        
        # If specific provider requested and available
        if request.provider and request.provider in self.providers:
            return request.provider
        
        # Provider selection logic (can be enhanced with more sophisticated logic)
        available_providers = list(self.providers.keys())
        
        if not available_providers:
            raise ProviderNotAvailableError("No providers available")
        
        # Simple selection logic - can be enhanced with:
        # - Load balancing
        # - Cost optimization
        # - Quality preferences
        # - Rate limiting awareness
        
        # For now, prefer Leonardo > Runware > Gemini > ComfyUI
        preference_order = [Provider.LEONARDO, Provider.RUNWARE, Provider.GEMINI, Provider.COMFYUI]
        
        for preferred_provider in preference_order:
            if preferred_provider in available_providers:
                return preferred_provider
        
        # Fallback to first available
        return available_providers[0]
    
    def validate_request_for_provider(self, request: UniversalImageRequest, provider: Provider) -> bool:
        """Validate if request is compatible with provider"""
        if provider not in self.providers:
            return False
        
        try:
            provider_instance = self.providers[provider]
            return provider_instance.validate_request(request)
        except Exception as e:
            logger.warning(f"Validation failed for {provider}: {e}")
            return False
    
    def save_generation_job(self, request: UniversalImageRequest, provider: Provider, generation_id: str) -> str:
        """Save generation job to database"""
        try:
            db = next(get_db())
            
            job = GenerationJob(
                generation_id=generation_id,
                provider=provider.value,
                project_id=request.project_id,
                prompt=request.prompt,
                negative_prompt=request.negative_prompt,
                width=request.width,
                height=request.height,
                num_images=request.num_images,
                model_id=request.model_id,
                preset_style=request.preset_style,
                seed=request.seed,
                guidance_scale=request.guidance_scale,
                steps=request.steps,
                provider_params=request.provider_params,
                status="pending"
            )
            
            db.add(job)
            db.commit()
            db.refresh(job)
            
            logger.info(f"Saved generation job: {job.id}")
            return str(job.id)
            
        except Exception as e:
            logger.error(f"Failed to save generation job: {e}")
            return str(uuid.uuid4())  # Fallback ID
        finally:
            if 'db' in locals():
                db.close()
    
    def update_generation_job(self, generation_id: str, provider: Provider, status: str, 
                            result_images: Optional[List] = None, error_message: Optional[str] = None):
        """Update generation job status"""
        try:
            db = next(get_db())
            
            job = db.query(GenerationJob).filter(
                GenerationJob.generation_id == generation_id,
                GenerationJob.provider == provider.value
            ).first()
            
            if job:
                job.status = status
                if result_images:
                    job.result_images = result_images
                if error_message:
                    job.error_message = error_message
                if status == "completed":
                    job.completed_at = datetime.utcnow()
                
                db.commit()
                logger.info(f"Updated generation job {generation_id}: {status}")
                
        except Exception as e:
            logger.error(f"Failed to update generation job: {e}")
        finally:
            if 'db' in locals():
                db.close()
    
    async def generate_with_provider(self, request: UniversalImageRequest, provider: Provider) -> UniversalImageResponse:
        """Generate images with a specific provider"""
        
        if provider not in self.providers:
            raise ProviderNotAvailableError(f"Provider {provider} not available")
        
        provider_instance = self.providers[provider]
        
        try:
            # Validate request
            if not self.validate_request_for_provider(request, provider):
                raise ImageGenerationError(f"Invalid request for provider {provider}", provider=provider)
            
            # Generate images
            logger.info(f"Generating with {provider}: {request.prompt[:100]}...")
            response = await provider_instance.generate_images(request)
            
            # Save/update job status
            self.update_generation_job(
                response.generation_id, 
                provider, 
                response.status.value,
                [img.dict() for img in response.images] if response.images else None,
                response.error_message
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Generation failed with {provider}: {e}")
            
            # Create error response
            error_response = UniversalImageResponse(
                generation_id=str(uuid.uuid4()),
                provider=provider,
                status=GenerationStatus.FAILED,
                prompt=request.prompt,
                project_id=request.project_id,
                images=[],
                total_images=0,
                created_at=datetime.utcnow(),
                error_message=str(e)
            )
            
            # Update job status
            self.update_generation_job(
                error_response.generation_id,
                provider,
                "failed",
                error_message=str(e)
            )
            
            return error_response
    
    async def validate_and_optimize_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Validate and optimize prompt before generation
        
        Returns:
            Dict containing validation results and optimized prompt
        """
        try:
            validation_response = await self.prompt_validator.validate_and_optimize(prompt)
            
            if validation_response.result == PromptValidationResult.TOO_LONG:
                return {
                    "success": False,
                    "error": validation_response.error_message,
                    "error_code": 400,
                    "validation_details": validation_response.to_dict()
                }
            
            return {
                "success": True,
                "optimized_prompt": validation_response.optimized_prompt,
                "validation_details": validation_response.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Prompt validation failed: {e}")
            return {
                "success": False,
                "error": f"Prompt validation error: {str(e)}",
                "error_code": 500,
                "validation_details": None
            }
    
    async def generate_images(self, request: UniversalImageRequest, 
                            enable_fallback: bool = True, 
                            max_retries: int = 2,
                            validate_prompt: bool = True) -> UniversalImageResponse:
        """
        Generate images with automatic provider selection, fallback, and prompt validation
        
        Args:
            request: Universal image generation request
            enable_fallback: Enable automatic fallback to other providers
            max_retries: Maximum number of providers to try
            validate_prompt: Enable prompt validation and optimization
        """
        
        # Validate and optimize prompt if enabled
        original_prompt = request.prompt
        validation_details = None
        
        if validate_prompt and request.prompt:
            logger.info(f"Validating prompt of length {len(request.prompt)}")
            
            validation_result = await self.validate_and_optimize_prompt(request.prompt)
            
            if not validation_result["success"]:
                # Return error response for prompt validation failure
                error_code = validation_result.get("error_code", 400)
                
                if error_code == 400:  # Prompt too long
                    return UniversalImageResponse(
                        generation_id=str(uuid.uuid4()),
                        provider=Provider.LEONARDO,
                        status=GenerationStatus.FAILED,
                        prompt=request.prompt,
                        project_id=request.project_id,
                        images=[],
                        total_images=0,
                        created_at=datetime.utcnow(),
                        error_message=validation_result["error"],
                        metadata={"validation_details": validation_result.get("validation_details")}
                    )
                else:
                    # For other errors, log but continue with original prompt
                    logger.warning(f"Prompt validation failed, continuing with original: {validation_result['error']}")
            else:
                # Use optimized prompt
                request.prompt = validation_result["optimized_prompt"]
                validation_details = validation_result["validation_details"]
                
                if request.prompt != original_prompt:
                    logger.info(f"Prompt optimized: {len(original_prompt)} → {len(request.prompt)} characters")
        
        providers_to_try = []
        
        providers_to_try = []
        
        # Select initial provider
        try:
            selected_provider = self.select_provider(request)
            providers_to_try.append(selected_provider)
        except Exception as e:
            logger.error(f"Provider selection failed: {e}")
            return UniversalImageResponse(
                generation_id=str(uuid.uuid4()),
                provider=Provider.LEONARDO,  # Default fallback
                status=GenerationStatus.FAILED,
                prompt=request.prompt,
                project_id=request.project_id,
                images=[],
                total_images=0,
                created_at=datetime.utcnow(),
                error_message=f"Provider selection failed: {str(e)}"
            )
        
        # Add fallback providers if enabled
        if enable_fallback:
            available_providers = list(self.providers.keys())
            for provider in available_providers:
                if provider not in providers_to_try and len(providers_to_try) < max_retries:
                    if self.validate_request_for_provider(request, provider):
                        providers_to_try.append(provider)
        
        # Try providers in order
        last_error = None
        
        for i, provider in enumerate(providers_to_try):
            try:
                logger.info(f"Attempting generation with {provider} (attempt {i+1}/{len(providers_to_try)})")
                
                # Save generation job
                generation_id = str(uuid.uuid4())
                self.save_generation_job(request, provider, generation_id)
                
                # Attempt generation
                response = await self.generate_with_provider(request, provider)
                
                if response.status == GenerationStatus.COMPLETED and response.images:
                    logger.info(f"Successfully generated {len(response.images)} images with {provider}")
                    
                    # Add validation details to response metadata
                    if validation_details:
                        if not response.metadata:
                            response.metadata = {}
                        response.metadata["prompt_validation"] = validation_details
                        response.metadata["original_prompt"] = original_prompt
                    
                    return response
                else:
                    last_error = response.error_message or f"Generation failed with {provider}"
                    logger.warning(f"Generation failed with {provider}: {last_error}")
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"Provider {provider} failed: {e}")
                
                if not enable_fallback or i == len(providers_to_try) - 1:
                    break  # No more providers to try
        
        # All providers failed
        logger.error(f"All providers failed. Last error: {last_error}")
        
        return UniversalImageResponse(
            generation_id=str(uuid.uuid4()),
            provider=providers_to_try[0] if providers_to_try else Provider.LEONARDO,
            status=GenerationStatus.FAILED,
            prompt=request.prompt,
            project_id=request.project_id,
            images=[],
            total_images=0,
            created_at=datetime.utcnow(),
            error_message=f"All providers failed. Last error: {last_error}"
        )
    
    async def batch_generate(self, requests: List[UniversalImageRequest]) -> List[UniversalImageResponse]:
        """Generate multiple image requests concurrently"""
        
        # Create tasks for concurrent generation
        tasks = [self.generate_images(request) for request in requests]
        
        # Execute concurrently with some reasonable limit
        semaphore = asyncio.Semaphore(3)  # Limit concurrent requests
        
        async def bounded_generate(request):
            async with semaphore:
                return await self.generate_images(request)
        
        bounded_tasks = [bounded_generate(request) for request in requests]
        results = await asyncio.gather(*bounded_tasks, return_exceptions=True)
        
        # Convert exceptions to error responses
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_response = UniversalImageResponse(
                    generation_id=str(uuid.uuid4()),
                    provider=Provider.LEONARDO,
                    status=GenerationStatus.FAILED,
                    prompt=requests[i].prompt,
                    project_id=requests[i].project_id,
                    images=[],
                    total_images=0,
                    created_at=datetime.utcnow(),
                    error_message=str(result)
                )
                final_results.append(error_response)
            else:
                final_results.append(result)
        
        return final_results
    
    async def get_prompt_validation_stats(self, prompt: str) -> Dict[str, Any]:
        """Get prompt analysis without optimization"""
        return await self.prompt_validator.get_optimization_stats(prompt)
    
    async def check_prompt_validator_availability(self) -> bool:
        """Check if Ollama prompt validator is available"""
        return await self.prompt_validator.check_ollama_availability()
    
    async def optimize_prompt_only(self, prompt: str) -> PromptValidationResponse:
        """Optimize prompt without generation"""
        return await self.prompt_validator.validate_and_optimize(prompt, force_optimize=True)
    
    async def close(self):
        """Close service and cleanup resources"""
        if hasattr(self, 'prompt_validator'):
            await self.prompt_validator.close()

# Global service instance
unified_service = UnifiedImageService()

def get_unified_service() -> UnifiedImageService:
    """Get the global unified image service instance"""
    return unified_service