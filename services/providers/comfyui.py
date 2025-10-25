"""
ComfyUI Local Server Provider
Local ComfyUI server integration for Flux Dev model
Requires ComfyUI server running locally with API enabled
"""

import os
import uuid
import requests
import logging
import json
import time
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from services.interfaces import (
    ImageProvider, UniversalImageRequest, UniversalImageResponse,
    GeneratedImage, Provider, GenerationStatus, ProviderConfig,
    ImageGenerationError, aspect_ratio_to_dimensions
)

logger = logging.getLogger(__name__)

class ComfyUIProvider(ImageProvider):
    """ComfyUI local server provider for Flux Dev model"""
    
    def __init__(self, base_url: Optional[str] = None):
        super().__init__(api_key=None, base_url=base_url or os.getenv("COMFYUI_URL", "http://localhost:8188"))
        self.provider_name = Provider.COMFYUI
        
        # ComfyUI doesn't use API keys, it's typically a local server
        self.headers = {"Content-Type": "application/json"}
        
        # Default Flux Dev workflow template
        self.flux_workflow_template = {
            "3": {
                "inputs": {
                    "seed": 42,
                    "steps": 20,
                    "cfg": 7.0,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                },
                "class_type": "KSampler",
                "_meta": {"title": "KSampler"}
            },
            "4": {
                "inputs": {
                    "ckpt_name": "flux1-dev-fp8.safetensors"
                },
                "class_type": "CheckpointLoaderSimple",
                "_meta": {"title": "Load Checkpoint"}
            },
            "5": {
                "inputs": {
                    "width": 512,
                    "height": 512,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage",
                "_meta": {"title": "Empty Latent Image"}
            },
            "6": {
                "inputs": {
                    "text": "a beautiful landscape",
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Prompt)"}
            },
            "7": {
                "inputs": {
                    "text": "",
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Negative)"}
            },
            "8": {
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2]
                },
                "class_type": "VAEDecode",
                "_meta": {"title": "VAE Decode"}
            },
            "9": {
                "inputs": {
                    "filename_prefix": "ComfyUI",
                    "images": ["8", 0]
                },
                "class_type": "SaveImage",
                "_meta": {"title": "Save Image"}
            }
        }
    
    def get_supported_models(self) -> List[Dict[str, Any]]:
        """Get list of supported ComfyUI models"""
        return [
            {
                "id": "flux-dev",
                "name": "Flux Dev",
                "description": "Flux development model via ComfyUI",
                "checkpoint": "flux1-dev-fp8.safetensors"
            }
        ]
    
    def validate_request(self, request: UniversalImageRequest) -> bool:
        """Validate request against ComfyUI capabilities"""
        # Check if ComfyUI server is accessible
        try:
            response = requests.get(f"{self.base_url}/system_stats", timeout=5)
            if response.status_code != 200:
                logger.error("ComfyUI server not accessible")
                return False
        except Exception as e:
            logger.error(f"Cannot connect to ComfyUI server: {e}")
            return False
        
        # Check dimensions (should be multiples of 8 for most models)
        if request.width and request.width % 8 != 0:
            return False
        if request.height and request.height % 8 != 0:
            return False
        
        # Check number of images (ComfyUI can handle multiple but we'll limit)
        if request.num_images > 4:
            return False
        
        return True
    
    def normalize_dimensions(self, width: int, height: int) -> tuple[int, int]:
        """Normalize dimensions to multiples of 8"""
        width = max(256, min(2048, (width // 8) * 8))
        height = max(256, min(2048, (height // 8) * 8))
        return width, height
    
    def map_request(self, request: UniversalImageRequest) -> Dict[str, Any]:
        """Map universal request to ComfyUI workflow format"""
        
        # Handle dimensions
        if request.aspect_ratio:
            width, height = aspect_ratio_to_dimensions(request.aspect_ratio, 512)
        else:
            width, height = request.width or 512, request.height or 512
        
        width, height = self.normalize_dimensions(width, height)
        
        # Create workflow from template
        workflow = json.loads(json.dumps(self.flux_workflow_template))  # Deep copy
        
        # Update workflow with request parameters
        workflow["5"]["inputs"]["width"] = width
        workflow["5"]["inputs"]["height"] = height
        workflow["5"]["inputs"]["batch_size"] = min(request.num_images, 4)
        
        workflow["6"]["inputs"]["text"] = request.prompt
        
        if request.negative_prompt:
            workflow["7"]["inputs"]["text"] = request.negative_prompt
        
        if request.seed:
            workflow["3"]["inputs"]["seed"] = request.seed
        
        if request.steps:
            workflow["3"]["inputs"]["steps"] = min(max(request.steps, 10), 100)
        
        if request.guidance_scale:
            workflow["3"]["inputs"]["cfg"] = request.guidance_scale
        
        # Update model if specified
        model_map = {
            "flux-dev": "flux1-dev-fp8.safetensors",
            # Add more models as needed
        }
        
        if request.model_id and request.model_id in model_map:
            workflow["4"]["inputs"]["ckpt_name"] = model_map[request.model_id]
        
        # Add provider-specific parameters
        if request.provider_params:
            # Allow overriding workflow parameters
            if "workflow_overrides" in request.provider_params:
                for node_id, overrides in request.provider_params["workflow_overrides"].items():
                    if node_id in workflow:
                        workflow[node_id]["inputs"].update(overrides)
        
        return {
            "prompt": workflow,
            "client_id": str(uuid.uuid4())
        }
    
    def map_response(self, provider_response: Dict[str, Any], request: UniversalImageRequest, prompt_id: str) -> UniversalImageResponse:
        """Map ComfyUI response to universal format"""
        
        images = []
        generation_id = prompt_id
        
        try:
            # ComfyUI response contains information about generated images
            if "images" in provider_response:
                for img_data in provider_response["images"]:
                    image = GeneratedImage(
                        id=str(uuid.uuid4()),
                        provider_id=img_data.get("filename"),
                        # ComfyUI saves images locally, we need to construct URL
                        url=f"{self.base_url}/view?filename={img_data.get('filename')}&subfolder={img_data.get('subfolder', '')}&type={img_data.get('type', 'output')}",
                        width=request.width,
                        height=request.height,
                        format="png",  # ComfyUI typically outputs PNG
                        provider_metadata={
                            "filename": img_data.get("filename"),
                            "subfolder": img_data.get("subfolder"),
                            "type": img_data.get("type"),
                            "prompt_id": prompt_id
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
                cost=0.0,  # Local generation is free
                provider_response=provider_response
            )
            
        except Exception as e:
            logger.error(f"Error processing ComfyUI response: {e}", exc_info=True)
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
    
    async def queue_prompt(self, workflow_data: Dict[str, Any]) -> str:
        """Queue a prompt in ComfyUI and return prompt ID"""
        try:
            response = requests.post(
                f"{self.base_url}/prompt",
                json=workflow_data,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("prompt_id")
            
        except Exception as e:
            logger.error(f"Failed to queue ComfyUI prompt: {e}")
            raise ImageGenerationError(f"Failed to queue prompt: {str(e)}", provider=self.provider_name)
    
    async def wait_for_completion(self, prompt_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for ComfyUI to complete generation"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check queue status
                response = requests.get(f"{self.base_url}/queue", timeout=10)
                response.raise_for_status()
                queue_data = response.json()
                
                # Check if our prompt is still in queue
                running = queue_data.get("queue_running", [])
                pending = queue_data.get("queue_pending", [])
                
                prompt_in_queue = False
                for item in running + pending:
                    if len(item) > 1 and item[1] == prompt_id:
                        prompt_in_queue = True
                        break
                
                if not prompt_in_queue:
                    # Prompt completed, get history
                    history_response = requests.get(f"{self.base_url}/history/{prompt_id}", timeout=10)
                    history_response.raise_for_status()
                    
                    history = history_response.json()
                    if prompt_id in history:
                        return history[prompt_id]
                
                # Wait before next check
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.warning(f"Error checking ComfyUI status: {e}")
                await asyncio.sleep(5)
        
        raise ImageGenerationError(f"ComfyUI generation timeout after {timeout}s", provider=self.provider_name)
    
    async def generate_images(self, request: UniversalImageRequest) -> UniversalImageResponse:
        """Generate images using ComfyUI"""
        
        try:
            # Validate request
            if not self.validate_request(request):
                raise ImageGenerationError(
                    "Invalid request parameters for ComfyUI provider or server not accessible",
                    provider=self.provider_name
                )
            
            # Map to ComfyUI format
            workflow_data = self.map_request(request)
            
            logger.info(f"Queuing ComfyUI prompt: {request.prompt[:100]}...")
            
            # Queue the prompt
            prompt_id = await self.queue_prompt(workflow_data)
            if not prompt_id:
                raise ImageGenerationError("Failed to get prompt ID from ComfyUI", provider=self.provider_name)
            
            logger.info(f"ComfyUI prompt queued with ID: {prompt_id}")
            
            # Wait for completion
            result = await self.wait_for_completion(prompt_id)
            
            # Extract images from result
            images_data = []
            if "outputs" in result:
                for node_id, node_output in result["outputs"].items():
                    if "images" in node_output:
                        images_data.extend(node_output["images"])
            
            # Map response
            response_data = {"images": images_data, "prompt_id": prompt_id}
            return self.map_response(response_data, request, prompt_id)
            
        except ImageGenerationError:
            raise
        
        except Exception as e:
            error_msg = f"Unexpected error in ComfyUI provider: {str(e)}"
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

def create_comfyui_provider() -> ComfyUIProvider:
    """Factory function to create ComfyUI provider instance"""
    return ComfyUIProvider()

# Provider configuration for ComfyUI
COMFYUI_CONFIG = ProviderConfig(
    provider=Provider.COMFYUI,
    name="ComfyUI (Local)",
    description="Local ComfyUI server with Flux Dev model",
    base_url="http://localhost:8188",
    api_key_env="",  # No API key needed for local server
    default_model="flux-dev",
    supported_formats=["png", "jpg"],
    max_width=2048,
    max_height=2048,
    max_images=4,
    supports_negative_prompt=True,
    supports_seed=True,
    supports_steps=True,
    supports_guidance_scale=True,
    rate_limit_per_minute=None,  # No rate limits for local server
    rate_limit_per_hour=None,
    config_schema={
        "workflows": ["text-to-image"],
        "models": [
            {"id": "flux-dev", "name": "Flux Dev", "checkpoint": "flux1-dev-fp8.safetensors"}
        ],
        "samplers": ["euler", "euler_ancestral", "heun", "dpm_2", "dpm_2_ancestral"],
        "schedulers": ["normal", "karras", "exponential", "simple"],
        "requirements": "Local ComfyUI server with Flux model"
    }
)