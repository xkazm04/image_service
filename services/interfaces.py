"""
Universal interfaces for image generation providers
Defines common request/response formats and provider abstraction
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
import uuid
from datetime import datetime

# ============================================
# ENUMS AND CONSTANTS
# ============================================

class Provider(str, Enum):
    LEONARDO = "leonardo"
    RUNWARE = "runware"
    GEMINI = "gemini" 
    COMFYUI = "comfyui"

class OutputFormat(str, Enum):
    JPG = "jpg"
    PNG = "png"
    WEBP = "webp"

class AspectRatio(str, Enum):
    SQUARE = "1:1"
    LANDSCAPE = "16:9"
    PORTRAIT = "9:16"
    WIDE = "4:3"
    TALL = "3:4"

class GenerationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# ============================================
# UNIVERSAL REQUEST INTERFACE
# ============================================

class UniversalImageRequest(BaseModel):
    """Universal request format for all providers"""
    
    # Core generation parameters
    prompt: str = Field(..., min_length=1, max_length=3000, description="Text prompt for image generation")
    negative_prompt: Optional[str] = Field(None, max_length=3000, description="Negative prompt (what to avoid)")
    
    # Dimensions and format
    width: Optional[int] = Field(512, ge=128, le=2048, description="Image width")
    height: Optional[int] = Field(512, ge=128, le=2048, description="Image height")
    aspect_ratio: Optional[AspectRatio] = Field(None, description="Aspect ratio (overrides width/height for some providers)")
    
    # Generation settings
    num_images: int = Field(1, ge=1, le=20, description="Number of images to generate")
    seed: Optional[int] = Field(None, ge=1, le=9223372036854775807, description="Seed for reproducibility")
    
    # Quality and style
    model_id: Optional[str] = Field(None, description="Provider-specific model ID")
    preset_style: Optional[str] = Field("DYNAMIC", description="Style preset")
    guidance_scale: Optional[float] = Field(7.5, ge=1.0, le=30.0, description="How closely to follow prompt")
    steps: Optional[int] = Field(30, ge=10, le=100, description="Number of denoising steps")
    
    # Output preferences
    output_format: OutputFormat = Field(OutputFormat.PNG, description="Desired output format")
    
    # Provider selection and overrides
    provider: Optional[Provider] = Field(None, description="Specific provider to use")
    provider_params: Optional[Dict[str, Any]] = Field(None, description="Provider-specific parameters")
    
    # Metadata
    project_id: uuid.UUID = Field(..., description="Project ID for organization")
    scene_id: Optional[uuid.UUID] = Field(None, description="Scene ID for story context")

# ============================================
# UNIVERSAL RESPONSE INTERFACE
# ============================================

class GeneratedImage(BaseModel):
    """Individual generated image data"""
    
    # Identifiers
    id: str = Field(..., description="Unique image identifier")
    provider_id: Optional[str] = Field(None, description="Provider-specific image ID")
    
    # URLs and paths
    url: Optional[str] = Field(None, description="Original provider URL")
    local_url: Optional[str] = Field(None, description="Local serving URL")
    local_path: Optional[str] = Field(None, description="Local file path")
    
    # Generation metadata
    seed: Optional[int] = Field(None, description="Seed used for generation")
    model_id: Optional[str] = Field(None, description="Model used for generation")
    
    # File information
    width: Optional[int] = Field(None, description="Image width")
    height: Optional[int] = Field(None, description="Image height")
    format: Optional[str] = Field(None, description="File format")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    
    # Flags
    nsfw: Optional[bool] = Field(False, description="NSFW content detected")
    
    # Provider-specific data
    provider_metadata: Optional[Dict[str, Any]] = Field(None, description="Provider-specific metadata")

class UniversalImageResponse(BaseModel):
    """Universal response format for all providers"""
    
    # Generation info
    generation_id: str = Field(..., description="Generation job ID")
    provider: Provider = Field(..., description="Provider used")
    status: GenerationStatus = Field(..., description="Generation status")
    
    # Request context
    prompt: str = Field(..., description="Original prompt")
    project_id: uuid.UUID = Field(..., description="Project ID")
    
    # Results
    images: List[GeneratedImage] = Field(default=[], description="Generated images")
    total_images: int = Field(0, description="Total number of images generated")
    
    # Timing and cost
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Generation start time")
    completed_at: Optional[datetime] = Field(None, description="Generation completion time")
    cost: Optional[float] = Field(None, description="Generation cost")
    
    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Provider-specific data
    provider_response: Optional[Dict[str, Any]] = Field(None, description="Raw provider response")

# ============================================
# PROVIDER ABSTRACTION
# ============================================

class ImageProvider(ABC):
    """Abstract base class for image generation providers"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
        self.provider_name: Provider = None
    
    @abstractmethod
    async def generate_images(self, request: UniversalImageRequest) -> UniversalImageResponse:
        """Generate images based on universal request format"""
        pass
    
    @abstractmethod
    def map_request(self, request: UniversalImageRequest) -> Dict[str, Any]:
        """Map universal request to provider-specific format"""
        pass
    
    @abstractmethod
    def map_response(self, provider_response: Dict[str, Any], request: UniversalImageRequest) -> UniversalImageResponse:
        """Map provider response to universal format"""
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[Dict[str, Any]]:
        """Get list of supported models for this provider"""
        pass
    
    @abstractmethod
    def validate_request(self, request: UniversalImageRequest) -> bool:
        """Validate request against provider capabilities"""
        pass
    
    def normalize_dimensions(self, width: int, height: int) -> tuple[int, int]:
        """Normalize dimensions according to provider constraints"""
        return width, height
    
    def generate_task_id(self) -> str:
        """Generate a unique task ID for tracking"""
        return str(uuid.uuid4())

# ============================================
# PROVIDER CONFIGURATION
# ============================================

class ProviderConfig(BaseModel):
    """Configuration for a specific provider"""
    
    provider: Provider
    name: str
    description: str
    base_url: str
    api_key_env: str  # Environment variable name
    default_model: str
    
    # Capabilities
    supported_formats: List[OutputFormat]
    max_width: int
    max_height: int
    max_images: int
    supports_negative_prompt: bool = True
    supports_seed: bool = True
    supports_steps: bool = True
    supports_guidance_scale: bool = True
    
    # Rate limiting
    rate_limit_per_minute: Optional[int] = None
    rate_limit_per_hour: Optional[int] = None
    
    # Provider-specific configuration
    config_schema: Optional[Dict[str, Any]] = None
    
    is_enabled: bool = True

# ============================================
# ERROR HANDLING
# ============================================

class ImageGenerationError(Exception):
    """Base exception for image generation errors"""
    
    def __init__(self, message: str, provider: Optional[Provider] = None, status_code: Optional[int] = None):
        self.message = message
        self.provider = provider
        self.status_code = status_code
        super().__init__(self.message)

class ProviderNotAvailableError(ImageGenerationError):
    """Raised when a provider is not available"""
    pass

class InvalidRequestError(ImageGenerationError):
    """Raised when request is invalid for the provider"""
    pass

class RateLimitError(ImageGenerationError):
    """Raised when rate limit is exceeded"""
    pass

class GenerationTimeoutError(ImageGenerationError):
    """Raised when generation takes too long"""
    pass

# ============================================
# UTILITY FUNCTIONS
# ============================================

def aspect_ratio_to_dimensions(aspect_ratio: AspectRatio, base_size: int = 512) -> tuple[int, int]:
    """Convert aspect ratio to width/height dimensions"""
    ratios = {
        AspectRatio.SQUARE: (1, 1),
        AspectRatio.LANDSCAPE: (16, 9),
        AspectRatio.PORTRAIT: (9, 16),
        AspectRatio.WIDE: (4, 3),
        AspectRatio.TALL: (3, 4)
    }
    
    ratio_w, ratio_h = ratios[aspect_ratio]
    
    # Calculate dimensions maintaining aspect ratio
    if ratio_w >= ratio_h:
        width = base_size
        height = int(base_size * ratio_h / ratio_w)
    else:
        height = base_size
        width = int(base_size * ratio_w / ratio_h)
    
    # Ensure dimensions are multiples of 8 (common requirement)
    width = (width // 8) * 8
    height = (height // 8) * 8
    
    return width, height

def validate_dimensions(width: int, height: int, provider_config: ProviderConfig) -> bool:
    """Validate dimensions against provider constraints"""
    return (
        provider_config.max_width >= width >= 128 and
        provider_config.max_height >= height >= 128 and
        width % 8 == 0 and  # Most providers require multiples of 8
        height % 8 == 0
    )