"""
Ollama service package initialization
"""

from .client import (
    OllamaClient,
    OllamaConfig,
    OllamaRequest,
    OllamaResponse,
    get_ollama_client,
    close_global_client
)

__all__ = [
    "OllamaClient",
    "OllamaConfig", 
    "OllamaRequest",
    "OllamaResponse",
    "get_ollama_client",
    "close_global_client"
]