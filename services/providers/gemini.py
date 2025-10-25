"""
Gemini Image Generation Provider (Nano Banana)
Google Gemini 2.5 Flash image generation
API Documentation: https://ai.google.dev/gemini-api/docs/image-generation
"""

import os
import uuid
import requests
import logging
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime

from services.interfaces import (
    ImageProvider, UniversalImageRequest, UniversalImageResponse,
    GeneratedImage, Provider, GenerationStatus, ProviderConfig,
    ImageGenerationError, AspectRatio, aspect_ratio_to_dimensions
)

logger = logging.getLogger(__name__)

class GeminiProvider(ImageProvider):
    """Gemini image generation provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("GEMINI_API_KEY"))
        self.provider_name = Provider.GEMINI
        self.base_url = "https://generativelanguage.googleapis.com"
        self.model = "gemini-2.5-flash-image"
        
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY environment variable.")
    
    def get_supported_models(self) -> List[Dict[str, Any]]:
        """Get list of supported Gemini models"""
        return [
            {
                "id": "gemini-2.5-flash-image",
                "name": "Gemini 2.5 Flash Image",
                "description": "Fast image generation with Gemini 2.5 Flash"
            }
        ]
    
    def validate_request(self, request: UniversalImageRequest) -> bool:
        """Validate request against Gemini capabilities"""
        # Gemini has fewer constraints but some limitations
        
        # Check prompt length (reasonable limit)
        if len(request.prompt) < 1 or len(request.prompt) > 2000:
            return False
        
        # Gemini doesn't support multiple images in one call
        if request.num_images > 1:
            logger.warning("Gemini only supports 1 image per request. Will generate 1 image.")
        
        # Gemini doesn't support negative prompts
        if request.negative_prompt:
            logger.warning("Gemini doesn't support negative prompts. Ignoring negative_prompt.")
        
        # Gemini doesn't support seed
        if request.seed:
            logger.warning("Gemini doesn't support seed parameter. Ignoring seed.")
        
        return True
    
    def normalize_dimensions(self, width: int, height: int) -> tuple[int, int]:
        """Normalize dimensions - Gemini uses aspect ratios"""
        # Gemini works with aspect ratios, we'll store the requested dimensions
        # but the actual output size is determined by Gemini
        return width, height
    
    def map_request(self, request: UniversalImageRequest) -> Dict[str, Any]:
        """Map universal request to Gemini API format"""
        
        # Gemini uses a conversation-style format
        contents = [
            {
                "parts": [
                    {"text": f"Generate an image: {request.prompt}"}
                ]
            }
        ]
        
        # Determine aspect ratio
        aspect_ratio = "1:1"  # Default
        if request.aspect_ratio:
            aspect_ratio = request.aspect_ratio.value
        elif request.width and request.height:
            # Calculate aspect ratio from dimensions
            ratio = request.width / request.height
            if abs(ratio - 1.0) < 0.1:
                aspect_ratio = "1:1"
            elif abs(ratio - 16/9) < 0.1:
                aspect_ratio = "16:9"
            elif abs(ratio - 9/16) < 0.1:
                aspect_ratio = "9:16"
            elif abs(ratio - 4/3) < 0.1:
                aspect_ratio = "4:3"
            elif abs(ratio - 3/4) < 0.1:
                aspect_ratio = "3:4"
        
        gemini_request = {
            "contents": contents,
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "object",
                    "properties": {
                        "alt_text": {
                            "type": "string",
                            "description": "A description of the generated image"
                        }
                    }
                }
            }
        }
        
        # Add aspect ratio if supported
        if request.aspect_ratio or (request.width and request.height):
            # Note: Gemini's aspect ratio support may vary by version
            # This is a placeholder for when/if they support it in the generation config
            pass
        
        # Add provider-specific parameters
        if request.provider_params:
            gemini_request.update(request.provider_params)
        
        return gemini_request
    
    def map_response(self, provider_response: Dict[str, Any], request: UniversalImageRequest) -> UniversalImageResponse:
        """Map Gemini response to universal format"""
        
        images = []
        generation_id = str(uuid.uuid4())
        
        try:
            # Process Gemini response format
            candidates = provider_response.get("candidates", [])
            
            for candidate in candidates:
                content = candidate.get("content", {})
                parts = content.get("parts", [])
                
                for part in parts:
                    # Look for inline image data
                    if "inlineData" in part:
                        inline_data = part["inlineData"]
                        mime_type = inline_data.get("mimeType", "image/png")
                        base64_data = inline_data.get("data")
                        
                        if base64_data:
                            # Create image object
                            image = GeneratedImage(
                                id=str(uuid.uuid4()),
                                provider_id=generation_id,
                                # Note: Gemini provides base64 data, not URLs
                                url=None,
                                width=request.width or 1024,  # Gemini default
                                height=request.height or 1024,
                                format="png",  # Gemini typically returns PNG
                                provider_metadata={
                                    "mime_type": mime_type,
                                    "base64_data": base64_data[:100] + "..." if len(base64_data) > 100 else base64_data,
                                    "candidate_index": len(images)
                                }
                            )
                            images.append(image)
            
            # Extract usage metadata if available
            usage_metadata = provider_response.get("usageMetadata", {})
            
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
                cost=None,  # Gemini doesn't provide cost in response
                provider_response=provider_response
            )
            
        except Exception as e:
            logger.error(f"Error processing Gemini response: {e}", exc_info=True)
            return UniversalImageResponse(
                generation_id=generation_id,
                provider=self.provider_name,
                status=GenerationStatus.FAILED,
                prompt=request.prompt,
                project_id=request.project_id,
                images=[],
                total_images=0,
                created_at=datetime.utcnow(),
                error_message=f"Error processing response: {str(e)}",
                provider_response=provider_response
            )
    
    def save_base64_image(self, base64_data: str, image_id: str, project_id: str) -> Optional[str]:
        """Save base64 image data to local storage"""
        try:
            from utils.storage import LocalStorage
            storage = LocalStorage()
            
            # Decode base64 data
            image_data = base64.b64decode(base64_data)
            
            # Get file path
            local_path = storage.get_image_path(str(project_id), image_id, "png")
            
            # Save to file
            with open(local_path, 'wb') as f:
                f.write(image_data)
            
            # Get URL for serving
            local_url = storage.get_image_url(str(project_id), image_id)
            
            logger.info(f"Saved Gemini image to: {local_path}")
            return str(local_path), local_url
            
        except Exception as e:
            logger.error(f"Failed to save Gemini image: {e}")
            return None, None
    
    async def generate_images(self, request: UniversalImageRequest) -> UniversalImageResponse:
        """Generate images using Gemini API"""
        
        try:
            # Validate request
            if not self.validate_request(request):
                raise ImageGenerationError(
                    "Invalid request parameters for Gemini provider",
                    provider=self.provider_name
                )
            
            # Map to Gemini format
            gemini_request = self.map_request(request)
            
            logger.info(f"Sending Gemini request for prompt: {request.prompt[:100]}...")
            
            # Make API request
            url = f"{self.base_url}/v1beta/models/{self.model}:generateContent"
            params = {"key": self.api_key}
            
            response = requests.post(
                url,
                json=gemini_request,
                params=params,
                timeout=120  # Gemini can take longer
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            logger.info("Gemini response received successfully")
            
            # Map response
            universal_response = self.map_response(response_data, request)
            
            # Save base64 images to local storage
            for image in universal_response.images:
                if image.provider_metadata and "base64_data" in image.provider_metadata:
                    base64_data = response_data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
                    local_path, local_url = self.save_base64_image(
                        base64_data, image.id, str(request.project_id)
                    )
                    if local_path:
                        image.local_path = local_path
                        image.local_url = local_url
            
            return universal_response
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Gemini API request failed: {str(e)}"
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
            error_msg = f"Unexpected error in Gemini provider: {str(e)}"
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

def create_gemini_provider() -> GeminiProvider:
    """Factory function to create Gemini provider instance"""
    return GeminiProvider()

# Provider configuration for Gemini
GEMINI_CONFIG = ProviderConfig(
    provider=Provider.GEMINI,
    name="Gemini Image Generation",
    description="Google Gemini 2.5 Flash image generation with SynthID watermark",
    base_url="https://generativelanguage.googleapis.com",
    api_key_env="GEMINI_API_KEY",
    default_model="gemini-2.5-flash-image",
    supported_formats=["png"],  # Gemini typically returns PNG
    max_width=1024,  # Gemini default output size
    max_height=1024,
    max_images=1,  # One image per request
    supports_negative_prompt=False,
    supports_seed=False,
    supports_steps=False,
    supports_guidance_scale=False,
    rate_limit_per_minute=15,  # Conservative estimate
    rate_limit_per_hour=900,
    config_schema={
        "models": [
            {"id": "gemini-2.5-flash-image", "name": "Gemini 2.5 Flash Image"}
        ],
        "aspectRatios": ["1:1", "16:9", "9:16", "4:3", "3:4"],
        "features": ["SynthID watermark", "Multi-turn conversation", "Content safety"]
    }
)