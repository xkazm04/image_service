"""
Unified Image Generation Routes
Provides a single API endpoint that aggregates all providers
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from uuid import UUID

from database import get_db
from services.unified_generation import get_unified_service
from services.interfaces import (
    UniversalImageRequest, UniversalImageResponse, Provider,
    GenerationStatus, OutputFormat, AspectRatio
)
from models.models import GenerationJob
from pydantic import BaseModel, Field

router = APIRouter(tags=["Unified Generation"])
logger = logging.getLogger(__name__)

# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class QuickGenerationRequest(BaseModel):
    """Simplified request model for quick generation"""
    prompt: str = Field(..., min_length=1, max_length=10000, description="Text prompt for image generation (will be optimized if over 3000 chars)")
    project_id: UUID = Field(..., description="Project ID")
    
    # Optional parameters with sensible defaults
    negative_prompt: Optional[str] = Field(None, max_length=10000, description="What to avoid in generation (will be optimized if over 3000 chars)")
    width: Optional[int] = Field(512, ge=128, le=2048, description="Image width")
    height: Optional[int] = Field(512, ge=128, le=2048, description="Image height")
    num_images: Optional[int] = Field(1, ge=1, le=8, description="Number of images")
    provider: Optional[Provider] = Field(None, description="Specific provider to use")
    seed: Optional[int] = Field(None, description="Seed for reproducibility")
    
class BatchGenerationRequest(BaseModel):
    """Request for batch generation"""
    requests: List[UniversalImageRequest] = Field(..., max_items=10, description="List of generation requests")
    
class ProviderStatusResponse(BaseModel):
    """Response model for provider status"""
    providers: Dict[str, Dict[str, Any]]
    total_available: int
    
class GenerationJobResponse(BaseModel):
    """Response model for generation job status"""
    id: str
    generation_id: str
    provider: str
    status: str
    prompt: str
    created_at: str
    completed_at: Optional[str]
    error_message: Optional[str]
    result_images: Optional[List[Dict]] = None

# ============================================
# MAIN GENERATION ENDPOINTS
# ============================================

@router.post("/generate", response_model=UniversalImageResponse)
async def generate_images(
    request: UniversalImageRequest,
    enable_fallback: bool = True,
    max_retries: int = 2,
    background_tasks: BackgroundTasks = None
):
    """
    Generate images using the unified service
    
    This endpoint automatically selects the best available provider
    and can fallback to others if the primary provider fails.
    """
    try:
        service = get_unified_service()
        
        logger.info(f"Unified generation request: {request.prompt[:100]}... (Provider: {request.provider})")
        
        # Generate images
        response = await service.generate_images(
            request=request,
            enable_fallback=enable_fallback,
            max_retries=max_retries
        )
        
        logger.info(f"Generation completed with status: {response.status}")
        
        return response
        
    except Exception as e:
        logger.error(f"Unified generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Image generation failed: {str(e)}"
        )

@router.post("/generate/quick", response_model=UniversalImageResponse)
async def quick_generate(request: QuickGenerationRequest):
    """
    Quick image generation with simplified parameters
    
    This is a convenience endpoint that uses sensible defaults
    for most parameters.
    """
    try:
        # Convert to full request
        full_request = UniversalImageRequest(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            width=request.width,
            height=request.height,
            num_images=request.num_images,
            seed=request.seed,
            project_id=request.project_id,
            provider=request.provider
        )
        
        service = get_unified_service()
        response = await service.generate_images(full_request)
        
        return response
        
    except Exception as e:
        logger.error(f"Quick generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Quick generation failed: {str(e)}"
        )

@router.post("/generate/batch", response_model=List[UniversalImageResponse])
async def batch_generate(request: BatchGenerationRequest):
    """
    Generate multiple images concurrently
    
    Processes multiple generation requests in parallel with
    automatic load balancing across providers.
    """
    try:
        if len(request.requests) == 0:
            raise HTTPException(status_code=400, detail="No requests provided")
        
        if len(request.requests) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 requests per batch")
        
        service = get_unified_service()
        responses = await service.batch_generate(request.requests)
        
        logger.info(f"Batch generation completed: {len(responses)} responses")
        
        return responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Batch generation failed: {str(e)}"
        )

# ============================================
# PROVIDER MANAGEMENT ENDPOINTS
# ============================================

@router.get("/providers", response_model=ProviderStatusResponse)
async def get_provider_status():
    """Get status of all available providers"""
    try:
        service = get_unified_service()
        provider_status = service.get_provider_status()
        
        total_available = sum(1 for p in provider_status.values() if p.get("available", False))
        
        return ProviderStatusResponse(
            providers=provider_status,
            total_available=total_available
        )
        
    except Exception as e:
        logger.error(f"Failed to get provider status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get provider status: {str(e)}"
        )

@router.get("/providers/available")
async def get_available_providers():
    """Get list of available provider names"""
    try:
        service = get_unified_service()
        providers = service.get_available_providers()
        
        return {
            "providers": [provider.value for provider in providers],
            "count": len(providers)
        }
        
    except Exception as e:
        logger.error(f"Failed to get available providers: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get available providers: {str(e)}"
        )

# ============================================
# GENERATION JOB MANAGEMENT
# ============================================

@router.get("/jobs", response_model=List[GenerationJobResponse])
def get_generation_jobs(
    project_id: Optional[UUID] = None,
    provider: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get generation jobs with optional filtering"""
    try:
        query = db.query(GenerationJob)
        
        if project_id:
            query = query.filter(GenerationJob.project_id == project_id)
        if provider:
            query = query.filter(GenerationJob.provider == provider)
        if status:
            query = query.filter(GenerationJob.status == status)
        
        jobs = query.order_by(GenerationJob.created_at.desc()).limit(limit).all()
        
        return [
            GenerationJobResponse(
                id=str(job.id),
                generation_id=job.generation_id,
                provider=job.provider,
                status=job.status,
                prompt=job.prompt,
                created_at=job.created_at.isoformat() if job.created_at else "",
                completed_at=job.completed_at.isoformat() if job.completed_at else None,
                error_message=job.error_message,
                result_images=job.result_images
            )
            for job in jobs
        ]
        
    except Exception as e:
        logger.error(f"Failed to get generation jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get generation jobs: {str(e)}"
        )

@router.get("/jobs/{job_id}", response_model=GenerationJobResponse)
def get_generation_job(job_id: str, db: Session = Depends(get_db)):
    """Get specific generation job details"""
    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Generation job not found")
        
        return GenerationJobResponse(
            id=str(job.id),
            generation_id=job.generation_id,
            provider=job.provider,
            status=job.status,
            prompt=job.prompt,
            created_at=job.created_at.isoformat() if job.created_at else "",
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            error_message=job.error_message,
            result_images=job.result_images
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get generation job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get generation job: {str(e)}"
        )

# ============================================
# PROMPT VALIDATION ENDPOINTS
# ============================================

class PromptValidationRequest(BaseModel):
    """Request model for prompt validation"""
    prompt: str = Field(..., min_length=1, description="Prompt to validate")
    force_optimize: bool = Field(False, description="Force optimization even if under threshold")

class PromptValidationStatsResponse(BaseModel):
    """Response model for prompt analysis stats"""
    character_count: int
    word_count: int
    needs_optimization: bool
    exceeds_maximum: bool
    optimization_threshold: int
    maximum_length: int
    estimated_reduction_needed: int

class PromptOptimizationResponse(BaseModel):
    """Response model for prompt optimization"""
    success: bool
    result: str
    original_prompt: str
    optimized_prompt: str
    original_length: int
    optimized_length: int
    size_reduction: int
    reduction_percentage: float
    optimization_time: Optional[float]
    error_message: Optional[str]
    metadata: Optional[Dict[str, Any]]

@router.post("/validate-prompt", response_model=PromptOptimizationResponse)
async def validate_prompt(request: PromptValidationRequest):
    """
    Validate and optimize a prompt for image generation
    
    - Returns 400 error if prompt exceeds 10,000 characters
    - Optimizes prompts between 3,000 and 10,000 characters
    - Uses Ollama to preserve maximum concepts while reducing length
    """
    try:
        service = get_unified_service()
        
        # Check if Ollama is available for optimization
        if len(request.prompt) > 3000 or request.force_optimize:
            ollama_available = await service.check_prompt_validator_availability()
            if not ollama_available:
                raise HTTPException(
                    status_code=503,
                    detail="Prompt optimization service (Ollama) is not available. Please ensure Ollama is running on localhost:11434"
                )
        
        # Validate and optimize
        validation_response = await service.optimize_prompt_only(request.prompt)
        
        if validation_response.result.value == "too_long":
            raise HTTPException(
                status_code=400,
                detail=f"Prompt exceeds maximum length of 10,000 characters (current: {len(request.prompt)})"
            )
        
        return PromptOptimizationResponse(
            success=True,
            result=validation_response.result.value,
            original_prompt=validation_response.original_prompt,
            optimized_prompt=validation_response.optimized_prompt,
            original_length=validation_response.original_length,
            optimized_length=validation_response.optimized_length,
            size_reduction=validation_response.original_length - validation_response.optimized_length,
            reduction_percentage=round(((validation_response.original_length - validation_response.optimized_length) / validation_response.original_length) * 100, 2) if validation_response.original_length > 0 else 0,
            optimization_time=validation_response.optimization_time,
            error_message=validation_response.error_message,
            metadata=validation_response.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prompt validation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Prompt validation failed: {str(e)}"
        )

@router.post("/prompt-stats", response_model=PromptValidationStatsResponse)
async def get_prompt_stats(request: PromptValidationRequest):
    """
    Get analysis statistics for a prompt without optimization
    
    Returns character count, word count, and validation thresholds
    """
    try:
        service = get_unified_service()
        stats = await service.get_prompt_validation_stats(request.prompt)
        
        return PromptValidationStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get prompt stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get prompt stats: {str(e)}"
        )

@router.get("/prompt-validator/health")
async def check_prompt_validator():
    """Check if the prompt validation service (Ollama) is available"""
    try:
        service = get_unified_service()
        is_available = await service.check_prompt_validator_availability()
        
        return {
            "available": is_available,
            "service": "Ollama Prompt Validator",
            "url": "http://localhost:11434",
            "status": "healthy" if is_available else "unavailable"
        }
        
    except Exception as e:
        logger.error(f"Prompt validator health check failed: {e}")
        return {
            "available": False,
            "service": "Ollama Prompt Validator",
            "url": "http://localhost:11434",
            "status": "error",
            "error": str(e)
        }

# ============================================
# UTILITY ENDPOINTS
# ============================================

@router.get("/health")
async def health_check():
    """Health check for the unified generation service"""
    try:
        service = get_unified_service()
        providers = service.get_available_providers()
        
        return {
            "status": "healthy",
            "providers_available": len(providers),
            "providers": [p.value for p in providers],
            "service": "Unified Image Generation"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "Unified Image Generation"
        }

@router.get("/models")
async def get_supported_models():
    """Get all supported models across providers"""
    try:
        service = get_unified_service()
        all_models = {}
        
        for provider_key, provider_instance in service.providers.items():
            try:
                models = provider_instance.get_supported_models()
                all_models[provider_key.value] = models
            except Exception as e:
                logger.warning(f"Failed to get models for {provider_key}: {e}")
                all_models[provider_key.value] = []
        
        return all_models
        
    except Exception as e:
        logger.error(f"Failed to get supported models: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get supported models: {str(e)}"
        )

# ============================================
# CONFIGURATION ENDPOINTS  
# ============================================

@router.get("/config")
async def get_service_config():
    """Get unified service configuration"""
    try:
        service = get_unified_service()
        
        return {
            "providers": {
                provider_key.value: {
                    "name": config.name,
                    "description": config.description,
                    "max_images": config.max_images,
                    "supported_formats": config.supported_formats,
                    "max_width": config.max_width,
                    "max_height": config.max_height,
                    "supports_negative_prompt": config.supports_negative_prompt,
                    "supports_seed": config.supports_seed,
                    "supports_steps": config.supports_steps,
                    "supports_guidance_scale": config.supports_guidance_scale
                }
                for provider_key, config in service.provider_configs.items()
            },
            "defaults": {
                "width": 512,
                "height": 512,
                "num_images": 1,
                "output_format": "png",
                "guidance_scale": 7.5,
                "steps": 30
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get service config: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get service config: {str(e)}"
        )