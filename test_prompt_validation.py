"""
Test script for prompt validation and optimization functionality
Tests various scenarios including long prompts, optimization, and error handling
"""

import asyncio
import json
import time
from typing import Dict, Any

# Test the prompt validation system
async def test_prompt_validation():
    """Test the prompt validation and optimization system"""
    
    print("=== PROMPT VALIDATION AND OPTIMIZATION TEST ===\n")
    
    # Import our services
    try:
        from services.prompt_validation import get_prompt_validator, PromptValidationResult
        from services.ollama import OllamaConfig
        from utils.prompt_utils import analyze_prompt, validate_prompt_length, needs_optimization
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure you're running this from the image service directory")
        return
    
    # Test cases
    test_cases = [
        {
            "name": "Short valid prompt",
            "prompt": "A beautiful woman with long flowing hair in a digital art style",
            "expected_result": "valid"
        },
        {
            "name": "Medium prompt (needs optimization)",
            "prompt": "A stunningly beautiful, gorgeously detailed, highly intricate, masterful piece of digital art showing a breathtakingly gorgeous woman with long flowing hair, stunning blue eyes, perfect skin, wearing an elegant dress, standing in a magical forest with golden sunlight filtering through the trees, highly detailed background with intricate flowers and plants, photorealistic lighting, cinematic composition, award-winning photography, shot with Canon EOS R5, 85mm lens, f/1.4 aperture, shallow depth of field, bokeh background, professional lighting setup, color grading, post-processing, HDR, ultra high resolution, 8K, 4K, masterpiece quality, best quality ever seen, incredible detail, perfect composition" * 4,  # Make it long
            "expected_result": "optimized"
        },
        {
            "name": "Too long prompt (should fail)",
            "prompt": "This is a very long prompt that exceeds the maximum allowed length. " * 200,  # Make it >10k chars
            "expected_result": "too_long"
        }
    ]
    
    # Initialize validator with local Ollama config
    config = OllamaConfig(
        base_url="http://localhost:11434",
        default_model="gpt-oss:20b",
        timeout=120,
        max_retries=2
    )
    
    validator = get_prompt_validator(config)
    
    # Check Ollama availability
    print("🔍 Checking Ollama availability...")
    ollama_available = await validator.check_ollama_availability()
    
    if ollama_available:
        print("✅ Ollama is available at http://localhost:11434")
    else:
        print("❌ Ollama is not available. Some tests may fail.")
        print("   Please start Ollama with: ollama serve")
        print("   And ensure the model 'gpt-oss:20b' is available")
    
    print("\n" + "="*60)
    
    # Run test cases
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 TEST CASE {i}: {test_case['name']}")
        print("-" * 40)
        
        prompt = test_case["prompt"]
        expected = test_case["expected_result"]
        
        print(f"Prompt length: {len(prompt)} characters")
        print(f"Expected result: {expected}")
        
        # Test utility functions first
        print(f"\n🔍 Prompt Analysis:")
        analysis = analyze_prompt(prompt)
        print(f"  • Words: {analysis['word_count']}")
        print(f"  • Sentences: {analysis['sentence_count']}")
        print(f"  • Keywords: {analysis['keyword_count']}")
        print(f"  • Needs optimization: {analysis['needs_optimization']}")
        print(f"  • Exceeds maximum: {analysis['exceeds_maximum']}")
        print(f"  • Complexity score: {analysis['complexity_score']}")
        print(f"  • Readability score: {analysis['readability_score']}")
        
        # Test validation
        is_valid, error_msg = validate_prompt_length(prompt)
        print(f"\n📏 Length Validation:")
        print(f"  • Valid: {is_valid}")
        if error_msg:
            print(f"  • Error: {error_msg}")
        
        # Test optimization (if Ollama available)
        if ollama_available and (needs_optimization(prompt) or expected == "optimized"):
            print(f"\n🤖 Testing Optimization:")
            
            start_time = time.time()
            
            try:
                result = await validator.validate_and_optimize(prompt)
                optimization_time = time.time() - start_time
                
                print(f"  • Result: {result.result.value}")
                print(f"  • Time: {optimization_time:.2f}s")
                print(f"  • Original length: {result.original_length}")
                print(f"  • Optimized length: {result.optimized_length}")
                
                if result.optimized_prompt != result.original_prompt:
                    reduction = result.original_length - result.optimized_length
                    percentage = (reduction / result.original_length) * 100
                    print(f"  • Reduction: {reduction} chars ({percentage:.1f}%)")
                    print(f"  • Optimized prompt preview: {result.optimized_prompt[:100]}...")
                
                if result.error_message:
                    print(f"  • Error: {result.error_message}")
                
                # Check if result matches expectation
                matches_expected = result.result.value == expected
                print(f"  • ✅ Expected result: {'YES' if matches_expected else 'NO'}")
                
            except Exception as e:
                print(f"  • ❌ Optimization failed: {e}")
        
        else:
            print(f"\n⏭️  Skipping optimization (Ollama not available or not needed)")
        
        print("\n" + "="*60)
    
    # Test batch operations if Ollama is available
    if ollama_available:
        print(f"\n🔄 BATCH OPTIMIZATION TEST")
        print("-" * 40)
        
        batch_prompts = [
            "A simple portrait of a woman",
            "A highly detailed, masterpiece quality, professional photograph of a beautiful woman with intricate details" * 10,
            "Digital art, concept art, fantasy illustration" * 5
        ]
        
        batch_start = time.time()
        
        for i, prompt in enumerate(batch_prompts, 1):
            print(f"\nBatch item {i}: {len(prompt)} chars")
            try:
                result = await validator.validate_and_optimize(prompt)
                print(f"  Result: {result.result.value} ({result.original_length} → {result.optimized_length})")
            except Exception as e:
                print(f"  Error: {e}")
        
        batch_time = time.time() - batch_start
        print(f"\nBatch processing time: {batch_time:.2f}s")
    
    # Cleanup
    await validator.close()
    
    print(f"\n✅ Prompt validation testing completed!")

async def test_api_integration():
    """Test the API integration with prompt validation"""
    
    print("\n=== API INTEGRATION TEST ===\n")
    
    try:
        import httpx
        
        base_url = "http://localhost:8000"  # Adjust if your API runs on different port
        
        # Test API endpoints
        async with httpx.AsyncClient() as client:
            
            # Test prompt validation endpoint
            print("🔍 Testing /validate-prompt endpoint...")
            
            test_prompt = "A beautiful woman with flowing hair" * 50  # Make it need optimization
            
            response = await client.post(
                f"{base_url}/unified/validate-prompt",
                json={
                    "prompt": test_prompt,
                    "force_optimize": False
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Validation endpoint working")
                print(f"  • Result: {result['result']}")
                print(f"  • Original length: {result['original_length']}")
                print(f"  • Optimized length: {result['optimized_length']}")
                print(f"  • Reduction: {result['size_reduction']} chars")
            else:
                print(f"❌ Validation endpoint failed: {response.status_code}")
                print(f"   Response: {response.text}")
            
            # Test prompt stats endpoint
            print(f"\n📊 Testing /prompt-stats endpoint...")
            
            response = await client.post(
                f"{base_url}/unified/prompt-stats",
                json={"prompt": test_prompt},
                timeout=10.0
            )
            
            if response.status_code == 200:
                stats = response.json()
                print("✅ Stats endpoint working")
                print(f"  • Character count: {stats['character_count']}")
                print(f"  • Word count: {stats['word_count']}")
                print(f"  • Needs optimization: {stats['needs_optimization']}")
            else:
                print(f"❌ Stats endpoint failed: {response.status_code}")
            
            # Test health check
            print(f"\n🏥 Testing prompt validator health...")
            
            response = await client.get(f"{base_url}/unified/prompt-validator/health", timeout=10.0)
            
            if response.status_code == 200:
                health = response.json()
                print("✅ Health endpoint working")
                print(f"  • Available: {health['available']}")
                print(f"  • Status: {health['status']}")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                
    except ImportError:
        print("❌ httpx not available. Install with: pip install httpx")
    except Exception as e:
        print(f"❌ API test failed: {e}")
        print("   Make sure the FastAPI server is running on http://localhost:8000")

if __name__ == "__main__":
    print("🚀 Starting Prompt Validation Test Suite")
    print("Make sure Ollama is running: ollama serve")
    print("Make sure the model is available: ollama pull gpt-oss:20b")
    print("")
    
    # Run core validation tests
    asyncio.run(test_prompt_validation())
    
    # Run API integration tests
    asyncio.run(test_api_integration())
    
    print("\n🎉 All tests completed!")