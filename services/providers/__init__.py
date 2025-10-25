"""
Image Generation Providers
Unified interface for multiple image generation services
"""

from .runware import RunwareProvider, RUNWARE_CONFIG, create_runware_provider
from .gemini import GeminiProvider, GEMINI_CONFIG, create_gemini_provider  
from .comfyui import ComfyUIProvider, COMFYUI_CONFIG, create_comfyui_provider

# Import existing Leonardo provider if it exists
try:
    from ..leo.leo_image import LeonardoProvider, LEONARDO_CONFIG, create_leonardo_provider
except ImportError:
    # If Leonardo provider doesn't exist yet, we'll create a placeholder
    LeonardoProvider = None
    LEONARDO_CONFIG = None
    create_leonardo_provider = None

from ..interfaces import Provider, ProviderConfig

# Provider registry
PROVIDERS = {
    Provider.RUNWARE: {
        "class": RunwareProvider,
        "config": RUNWARE_CONFIG, 
        "factory": create_runware_provider
    },
    Provider.GEMINI: {
        "class": GeminiProvider,
        "config": GEMINI_CONFIG,
        "factory": create_gemini_provider  
    },
    Provider.COMFYUI: {
        "class": ComfyUIProvider,
        "config": COMFYUI_CONFIG,
        "factory": create_comfyui_provider
    }
}

# Add Leonardo if available
if LeonardoProvider:
    PROVIDERS[Provider.LEONARDO] = {
        "class": LeonardoProvider,
        "config": LEONARDO_CONFIG,
        "factory": create_leonardo_provider
    }

def get_available_providers() -> dict:
    """Get all available providers"""
    return PROVIDERS

def get_provider_configs() -> list[ProviderConfig]:
    """Get configurations for all providers"""
    return [provider_info["config"] for provider_info in PROVIDERS.values() if provider_info["config"]]

def create_provider(provider: Provider, **kwargs):
    """Factory function to create a provider instance"""
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}")
    
    factory = PROVIDERS[provider]["factory"]
    if factory:
        return factory(**kwargs)
    else:
        provider_class = PROVIDERS[provider]["class"]
        return provider_class(**kwargs)

__all__ = [
    "RunwareProvider", "RUNWARE_CONFIG", "create_runware_provider",
    "GeminiProvider", "GEMINI_CONFIG", "create_gemini_provider", 
    "ComfyUIProvider", "COMFYUI_CONFIG", "create_comfyui_provider",
    "LeonardoProvider", "LEONARDO_CONFIG", "create_leonardo_provider",
    "PROVIDERS", "get_available_providers", "get_provider_configs", "create_provider"
]