"""
Reusable Ollama client service for AI model interactions.
Provides universal interface for various AI tasks with comprehensive error handling.
"""

import asyncio
import json
import logging
import time
from typing import Optional, Dict, Any, List
import httpx

logger = logging.getLogger(__name__)

class OllamaConfig:
    """Configuration for Ollama client"""
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: str = "gpt-oss:20b",
        timeout: int = 300,  # 5 minutes
        max_retries: int = 3
    ):
        self.base_url = base_url
        self.default_model = default_model
        self.timeout = timeout
        self.max_retries = max_retries

class OllamaRequest:
    """Universal request format for Ollama interactions"""
    def __init__(
        self,
        prompt: str,
        model: Optional[str] = None,
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.prompt = prompt
        self.model = model
        self.stream = stream
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.context = context or {}

class OllamaResponse:
    """Universal response format for Ollama interactions"""
    def __init__(
        self,
        success: bool,
        response: Optional[str] = None,
        model: Optional[str] = None,
        created_at: Optional[str] = None,
        done: bool = False,
        total_duration: Optional[int] = None,
        load_duration: Optional[int] = None,
        prompt_eval_count: Optional[int] = None,
        prompt_eval_duration: Optional[int] = None,
        eval_count: Optional[int] = None,
        eval_duration: Optional[int] = None,
        error: Optional[str] = None,
        error_code: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.response = response
        self.model = model
        self.created_at = created_at
        self.done = done
        self.total_duration = total_duration
        self.load_duration = load_duration
        self.prompt_eval_count = prompt_eval_count
        self.prompt_eval_duration = prompt_eval_duration
        self.eval_count = eval_count
        self.eval_duration = eval_duration
        self.error = error
        self.error_code = error_code
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary"""
        return {
            "success": self.success,
            "response": self.response,
            "model": self.model,
            "created_at": self.created_at,
            "done": self.done,
            "total_duration": self.total_duration,
            "load_duration": self.load_duration,
            "prompt_eval_count": self.prompt_eval_count,
            "prompt_eval_duration": self.prompt_eval_duration,
            "eval_count": self.eval_count,
            "eval_duration": self.eval_duration,
            "error": self.error,
            "error_code": self.error_code,
            "metadata": self.metadata
        }

class OllamaClient:
    """Universal Ollama client with comprehensive error handling and retry logic"""
    
    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig()
        self._client = None
        
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
        return self._client
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def check_availability(self) -> bool:
        """Check if Ollama is available and responsive"""
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.config.base_url}/api/tags",
                timeout=5.0  # Quick health check
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama availability check failed: {e}")
            return False
    
    async def get_available_models(self) -> List[str]:
        """Get list of available models from Ollama"""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.config.base_url}/api/tags")
            response.raise_for_status()
            
            data = response.json()
            return [model.get("name", "") for model in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return []
    
    async def generate(
        self,
        request: OllamaRequest,
        task_id: Optional[str] = None
    ) -> OllamaResponse:
        """Generate text using Ollama with comprehensive error handling"""
        
        start_time = time.time()
        task_id = task_id or f"ollama_{int(time.time())}_{id(request)}"
        
        logger.info(f"Starting Ollama generation task {task_id}")
        
        # Validate availability first
        if not await self.check_availability():
            error_msg = f"Ollama is not available at {self.config.base_url}"
            logger.error(error_msg)
            return OllamaResponse(
                success=False,
                error=error_msg,
                error_code=503,
                metadata={"task_id": task_id, "duration": time.time() - start_time}
            )
        
        # Prepare request payload
        payload = {
            "model": request.model or self.config.default_model,
            "prompt": request.prompt,
            "stream": request.stream,
            "options": {
                "temperature": request.temperature
            }
        }
        
        if request.max_tokens:
            payload["options"]["num_predict"] = request.max_tokens
            
        if request.system_prompt:
            payload["system"] = request.system_prompt
        
        # Retry logic
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                logger.info(f"Attempt {attempt + 1}/{self.config.max_retries} for task {task_id}")
                
                client = await self._get_client()
                response = await client.post(
                    f"{self.config.base_url}/api/generate",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    error_text = await response.aread() if hasattr(response, 'aread') else response.text
                    error_msg = f"Ollama API error ({response.status_code}): {error_text}"
                    logger.error(error_msg)
                    
                    if attempt == self.config.max_retries - 1:  # Last attempt
                        return OllamaResponse(
                            success=False,
                            error=error_msg,
                            error_code=response.status_code,
                            metadata={"task_id": task_id, "duration": time.time() - start_time}
                        )
                    continue
                
                # Parse response
                result = response.json()
                duration = time.time() - start_time
                
                logger.info(f"Task {task_id} completed successfully in {duration:.2f}s")
                
                return OllamaResponse(
                    success=True,
                    response=result.get("response"),
                    model=result.get("model"),
                    created_at=result.get("created_at"),
                    done=result.get("done", False),
                    total_duration=result.get("total_duration"),
                    load_duration=result.get("load_duration"),
                    prompt_eval_count=result.get("prompt_eval_count"),
                    prompt_eval_duration=result.get("prompt_eval_duration"),
                    eval_count=result.get("eval_count"),
                    eval_duration=result.get("eval_duration"),
                    metadata={
                        "task_id": task_id,
                        "duration": duration,
                        "attempts": attempt + 1,
                        "prompt_length": len(request.prompt),
                        "response_length": len(result.get("response", ""))
                    }
                )
                
            except asyncio.TimeoutError:
                error_msg = f"Timeout after {self.config.timeout}s"
                logger.error(f"Task {task_id} timeout: {error_msg}")
                last_error = error_msg
                
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(f"Task {task_id} error: {error_msg}")
                last_error = error_msg
                
            # Wait before retry (exponential backoff)
            if attempt < self.config.max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
        
        # All attempts failed
        duration = time.time() - start_time
        return OllamaResponse(
            success=False,
            error=last_error or "All retry attempts failed",
            metadata={"task_id": task_id, "duration": duration, "attempts": self.config.max_retries}
        )
    
    def parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from Ollama response with fallback handling"""
        try:
            # Try to extract JSON from markdown code blocks first
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if not json_match:
                json_match = re.search(r'```\s*(.*?)\s*```', response_text, re.DOTALL)
            
            json_string = json_match.group(1) if json_match else response_text
            return {"success": True, "data": json.loads(json_string.strip())}
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse JSON: {str(e)}",
                "raw_response": response_text
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected parsing error: {str(e)}",
                "raw_response": response_text
            }

# Global client instance for convenience
_global_client = None

def get_ollama_client(config: Optional[OllamaConfig] = None) -> OllamaClient:
    """Get global Ollama client instance"""
    global _global_client
    if _global_client is None:
        _global_client = OllamaClient(config)
    return _global_client

async def close_global_client():
    """Close global client"""
    global _global_client
    if _global_client:
        await _global_client.close()
        _global_client = None