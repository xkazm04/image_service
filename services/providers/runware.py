"""
Runware AI Image Generation Provider
Fast and scalable AI image generation with multiple models
API Documentation: https://runware.ai/docs/en/image-inference/api-reference
"""

import os
import uuid
import requests
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from services.interfaces import (
    ImageProvider, UniversalImageRequest, UniversalImageResponse,
    GeneratedImage, Provider, GenerationStatus, ProviderConfig,
    ImageGenerationError, aspect_ratio_to_dimensions
)

logger = logging.getLogger(__name__)

class RunwareProvider(ImageProvider):
    """Runware AI image generation provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("RUNWARE_API_KEY"))
        self.provider_name = Provider.RUNWARE
        self.base_url = "https://api.runware.ai"
        
        if not self.api_key:
            raise ValueError("Runware API key is required. Set RUNWARE_API_KEY environment variable.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_supported_models(self) -> List[Dict[str, Any]]:
        """Get list of supported Runware models"""
        return [
            {"id": "runware:100@1", "name": "Runware v1.0", "description": "High-quality general purpose model"},
            {"id": "runware:101@1", "name": "Runware v1.1", "description": "Enhanced model with better prompt adherence"},
        ]
    
    def validate_request(self, request: UniversalImageRequest) -> bool:
        """Validate request against Runware capabilities"""
        # Check dimensions (128-2048, divisible by 64)
        if request.width and (request.width < 128 or request.width > 2048 or request.width % 64 != 0):
            return False
        if request.height and (request.height < 128 or request.height > 2048 or request.height % 64 != 0):
            return False
        
        # Check number of images (1-20)
        if request.num_images < 1 or request.num_images > 20:
            return False
        
        # Check prompt length (2-3000 characters)
        if len(request.prompt) < 2 or len(request.prompt) > 3000:
            return False
        
        return True
    
    def normalize_dimensions(self, width: int, height: int) -> tuple[int, int]:
        """Normalize dimensions to Runware requirements (divisible by 64)"""
        width = max(128, min(2048, (width // 64) * 64))
        height = max(128, min(2048, (height // 64) * 64))
        return width, height
    
    def map_request(self, request: UniversalImageRequest) -> Dict[str, Any]:
        """Map universal request to Runware API format"""
        
        # Handle dimensions
        if request.aspect_ratio:
            width, height = aspect_ratio_to_dimensions(request.aspect_ratio, 512)
        else:
            width, height = request.width or 512, request.height or 512
        
        width, height = self.normalize_dimensions(width, height)
        
        # Map output format
        output_format_map = {
            "jpg": "JPG",
            "png": "PNG", 
            "webp": "WEBP"
        }
        
        runware_request = {
            "taskType": "imageInference",
            "taskUUID": self.generate_task_id(),
            "positivePrompt": request.prompt,
            "model": request.model_id or "runware:100@1",
            "width": width,
            "height": height,
            "numberResults": request.num_images,
            "outputType": "URL",  # We'll always use URL for consistency
            "outputFormat": output_format_map.get(request.output_format, "PNG"),
        }
        
        # Add optional parameters
        if request.negative_prompt:
            runware_request["negativePrompt"] = request.negative_prompt
        
        if request.seed:
            runware_request["seed"] = request.seed
        
        if request.guidance_scale:
            runware_request["CFGScale"] = request.guidance_scale
        
        if request.steps:
            runware_request["steps"] = request.steps
        
        # Add provider-specific parameters
        if request.provider_params:
            runware_request.update(request.provider_params)
        
        return runware_request
    
    def map_response(self, provider_response: Dict[str, Any], request: UniversalImageRequest) -> UniversalImageResponse:
        """Map Runware response to universal format"""
        
        images = []
        generation_id = provider_response.get("taskUUID", str(uuid.uuid4()))
        
        # Process response data
        if "data" in provider_response and isinstance(provider_response["data"], list):
            for item in provider_response["data"]:
                if item.get("taskType") == "imageInference":
                    image = GeneratedImage(
                        id=str(uuid.uuid4()),
                        provider_id=item.get("imageUUID"),
                        url=item.get("imageURL"),
                        seed=item.get("seed"),
                        width=request.width,
                        height=request.height,
                        format=request.output_format.lower(),
                        provider_metadata={
                            "cost": item.get("cost"),
                            "taskUUID": item.get("taskUUID"),
                            "imageUUID": item.get("imageUUID")
                        }
                    )
                    images.append(image)
        
        return UniversalImageResponse(
            generation_id=generation_id,
            provider=self.provider_name,
            status=GenerationStatus.COMPLETED if images else GenerationStatus.FAILED,
            prompt=request.prompt,
            project_id=request.project_id,
            images=images,
            total_images=len(images),
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            cost=sum(img.provider_metadata.get("cost", 0) for img in images if img.provider_metadata),
            provider_response=provider_response
        )
    
    async def generate_images(self, request: UniversalImageRequest) -> UniversalImageResponse:
        """Generate images using Runware API"""
        
        try:
            # Validate request
            if not self.validate_request(request):
                raise ImageGenerationError(
                    "Invalid request parameters for Runware provider",
                    provider=self.provider_name
                )
            
            # Map to Runware format
            runware_request = self.map_request(request)
            
            logger.info(f"Sending Runware request: {runware_request}")
            
            # Make API request
            response = requests.post(
                f"{self.base_url}/v1",
                json=[runware_request],  # Runware expects an array
                headers=self.headers,
                timeout=60
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            logger.info(f"Runware response received: {response_data}")
            
            # Map response
            return self.map_response(response_data, request)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Runware API request failed: {str(e)}"
            logger.error(error_msg)
            
            return UniversalImageResponse(
                generation_id=str(uuid.uuid4()),
                provider=self.provider_name,
                status=GenerationStatus.FAILED,
                prompt=request.prompt,
                project_id=request.project_id,
                images=[],
                total_images=0,
                created_at=datetime.utcnow(),
                error_message=error_msg,
                provider_response={"error": str(e)}
            )
        
        except Exception as e:
            error_msg = f"Unexpected error in Runware provider: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return UniversalImageResponse(
                generation_id=str(uuid.uuid4()),
                provider=self.provider_name,
                status=GenerationStatus.FAILED,
                prompt=request.prompt,
                project_id=request.project_id,
                images=[],
                total_images=0,
                created_at=datetime.utcnow(),
                error_message=error_msg,
                provider_response={"error": str(e)}
            )

def create_runware_provider() -> RunwareProvider:
    """Factory function to create Runware provider instance"""
    return RunwareProvider()

# Provider configuration for Runware
RUNWARE_CONFIG = ProviderConfig(
    provider=Provider.RUNWARE,
    name="Runware AI",
    description="Fast and scalable AI image generation with multiple models",
    base_url="https://api.runware.ai",
    api_key_env="RUNWARE_API_KEY",
    default_model="runware:100@1",
    supported_formats=["jpg", "png", "webp"],
    max_width=2048,
    max_height=2048,
    max_images=20,
    supports_negative_prompt=True,
    supports_seed=True,
    supports_steps=True,
    supports_guidance_scale=True,
    rate_limit_per_minute=60,
    rate_limit_per_hour=3600,
    config_schema={
        "outputTypes": ["URL", "base64Data", "dataURI"],
        "models": [
            {"id": "runware:100@1", "name": "Runware v1.0"},
            {"id": "runware:101@1", "name": "Runware v1.1"}
        ],
        "dimension_requirements": "Divisible by 64, range 128-2048"
    }
)