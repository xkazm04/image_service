# Image Generation API Providers Comparison

## Overview
This document compares three major image generation API providers:
- **Runware**: https://runware.ai/docs/en/image-inference/api-reference
- **Gemini (Nano Banana)**: https://ai.google.dev/gemini-api/docs/image-generation
- **Leonardo AI**: https://docs.leonardo.ai/docs/generate-your-first-images

## Table 2: Request Parameters mapping

| Parameter | Runware | Gemini (Nano Banana) | Leonardo AI | Mapping Notes |
|-----------|---------|---------------------|-------------|---------------|
| **CORE GENERATION** |
| Prompt (positive) | `positivePrompt` (string, 2-3000 chars) | `contents` (text part in array) | `prompt` (string) | ✅ **Mappable** - all support text prompts |
| Negative Prompt | `negativePrompt` (string, 2-3000 chars) | ❌ N/A | `negative_prompt` (string) | ⚠️ **Partial** - Gemini doesn't support |
| Model ID | `model` (AIR string) | `model` (fixed: gemini-2.5-flash-image) | `modelId` (UUID string) | ⚠️ **Provider-specific** - different ID systems |
| Width | `width` (128-2048, div by 64) | Via `aspectRatio` or default | `width` (32-1024, div by 8) | ⚠️ **Partial** - different ranges/methods |
| Height | `height` (128-2048, div by 64) | Via `aspectRatio` or default | `height` (32-1024, div by 8) | ⚠️ **Partial** - different ranges/methods |
| Number of Images | `numberResults` (1-20) | Via multiple calls or config | `num_images` (integer) | ✅ **Mappable** - similar concept |
| Seed | `seed` (1 to 9.2e18) | ❌ N/A | `seed` (integer) | ⚠️ **Partial** - Gemini doesn't support 
| **OUTPUT FORMAT** |
| Output Type | `outputType` (URL/base64/dataURI) | Returns base64 in response | Returns URL after polling | ⚠️ **Different mechanisms** |
| Output Format | `outputFormat` (JPG/PNG/WEBP) | PNG default | PNG/JPG | ⚠️ **Partial** - different options |
| Aspect Ratio | Via width/height | `aspectRatio` (1:1, 16:9, etc.) | Via width/height | ⚠️ **Different approaches** |


**Legend:**
- ✅ **Mappable**: Can be directly mapped across all providers
- ⚠️ **Partial**: Exists in some providers or requires transformation
- ❌ **Unique**: Provider-specific, no equivalent

---

## Generation Mechanism Analysis

### 1. **Runware** - Synchronous Response via WebSocket/HTTP

**Flow:**
```
1. POST request to /imageInference endpoint
2. Immediate processing (or queue)
3. Response returned directly with image data
   └─ Response format controlled by outputType:
      • URL: Returns imageURL
      • base64Data: Returns imageBase64Data
      • dataURI: Returns imageDataURI
```

**Key Characteristics:**
- **Synchronous by default**: Single request-response cycle
- **Task UUID matching**: Client provides UUID to match async responses
- **Parallel processing**: Multiple tasks can be sent simultaneously
- **Optional webhook**: Can specify `uploadEndpoint` for automatic upload
- **Response structure**:
```json
{
  "data": [{
    "taskType": "imageInference",
    "taskUUID": "a770f077-f413-47de-9dac-be0b26a35da6",
    "imageUUID": "77da2d99-a6d3-44d9-b8c0-ae9fb06b6200",
    "imageURL": "https://im.runware.ai/image/...",
    "seed": 12345,
    "cost": 0.0013
  }]
}
```

**Advantages:**
- No polling required for basic use
- Immediate results when processing is complete
- Multiple output format options

**Disadvantages:**
- May have longer wait times for single requests
- Connection needs to stay open for response

---

### 2. **Gemini (Nano Banana)** - Synchronous with Inline Response

**Flow:**
```
1. POST to /v1beta/models/gemini-2.5-flash-image:generateContent
2. Processing (wait for response)
3. Inline base64 image data in response
   └─ Image embedded in response.candidates[0].content.parts[]
```

**Key Characteristics:**
- **Fully synchronous**: Wait for complete response
- **Inline data**: Images returned as base64 in response body
- **Conversational**: Can continue in multi-turn for iterations
- **Response structure**:
```json
{
  "candidates": [{
    "content": {
      "parts": [
        {"text": "description text"},
        {
          "inlineData": {
            "mimeType": "image/png",
            "data": "<base64_encoded_image>"
          }
        }
      ]
    }
  }],
  "usageMetadata": {
    "promptTokenCount": 15,
    "candidatesTokenCount": 1290,
    "totalTokenCount": 1305
  }
}
```

**Advantages:**
- Simple integration (standard REST)
- No need for polling or separate retrieval
- Built-in multi-turn conversation support
- SynthID watermark for content provenance

**Disadvantages:**
- Must wait for entire processing to complete
- Large base64 payloads in response
- Limited customization compared to others
- No seed control for reproducibility

---

### 3. **Leonardo AI** - Asynchronous with Polling

**Flow:**
```
1. POST to /api/rest/v1/generations
   └─ Returns: {"sdGenerationJob": {"generationId": "123..."}}

2. Poll GET /api/rest/v1/generations/{generationId}
   └─ Check: generations_by_pk.status
   └─ Status values: "PENDING", "PROCESSING", "COMPLETE", "FAILED"

3. When status = "COMPLETE":
   └─ Extract: generations_by_pk.generated_images[]
      └─ Each image has: {id, url, likeCount, nsfw}

Optional: Set up webhook for automatic notification
```

**Key Characteristics:**
- **Fully asynchronous**: Immediate return of generation ID
- **Required polling**: Must query for completion
- **Webhook support**: Can avoid polling with callbacks
- **Response structure (initial)**:
```json
{
  "sdGenerationJob": {
    "generationId": "123456-0987-aaaa-bbbb-01010101010",
    "apiCreditCost": 7
  }
}
```

**Response structure (polling)**:
```json
{
  "generations_by_pk": {
    "id": "123456-0987-aaaa-bbbb-01010101010",
    "status": "COMPLETE",
    "generated_images": [
      {
        "id": "image-uuid-1",
        "url": "https://cdn.leonardo.ai/users/.../image.jpg",
        "likeCount": 0,
        "nsfw": false
      }
    ],
    "modelId": "model-uuid",
    "prompt": "original prompt",
    "negativePrompt": "...",
    "imageHeight": 768,
    "imageWidth": 1024,
    "inferenceSteps": 30,
    "seed": 42,
    "public": false,
    "scheduler": "LEONARDO",
    "presetStyle": "CINEMATIC",
    "createdAt": "2024-10-25T12:00:00.000Z"
  }
}
```

**Advantages:**
- Non-blocking: Client doesn't wait
- Scalable for batch operations
- Webhook support reduces polling overhead
- Detailed generation metadata returned

**Disadvantages:**
- More complex implementation
- Requires polling logic or webhook setup
- Multiple API calls per generation
- Potential delays in checking status