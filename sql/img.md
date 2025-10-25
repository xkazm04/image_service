# Image Generation API Providers Comparison

## Overview
This document compares three major image generation API providers:
- **Runware**: https://runware.ai/docs/en/image-inference/api-reference
- **Gemini (Nano Banana)**: https://ai.google.dev/gemini-api/docs/image-generation
- **Leonardo AI**: https://docs.leonardo.ai/docs/generate-your-first-images

---

## Table 1: Features Comparison

| Feature Category | Runware | Gemini (Nano Banana) | Leonardo AI |
|-----------------|---------|---------------------|-------------|
| **TEXT-TO-IMAGE** | ✅ Yes | ✅ Yes | ✅ Yes |
| **IMAGE-TO-IMAGE** | ✅ Yes (with strength control) | ✅ Yes (editing mode) | ✅ Yes (with init image) |
| **INPAINTING** | ✅ Yes (with mask image) | ✅ Yes (semantic masking) | ✅ Yes (via ControlNet) |
| **OUTPAINTING** | ✅ Yes (with pixel extensions) | ❌ No | ❌ No |
| **STYLE TRANSFER** | ✅ Yes (via LoRA, IP-Adapters) | ✅ Yes (conversational) | ✅ Yes (via Style Reference) |
| **CHARACTER REFERENCE** | ✅ Yes (PuLID, ACE++) | ❌ Limited | ✅ Yes (Character Reference) |
| **CONTENT REFERENCE** | ✅ Yes (IP-Adapters) | ✅ Yes (multi-image input) | ✅ Yes (Content Reference) |
| **CONTROLNET** | ✅ Yes (multiple simultaneous) | ❌ No | ✅ Yes (multiple ControlNets) |
| **LORA SUPPORT** | ✅ Yes (multiple LoRAs) | ❌ No | ❌ No (Elements instead) |
| **EMBEDDINGS** | ✅ Yes (Textual Inversion) | ❌ No | ❌ No |
| **PROMPT ENHANCEMENT** | ✅ Yes (prompt weighting) | ❌ No | ✅ Yes (Prompt Magic, Enhance) |
| **NEGATIVE PROMPTS** | ✅ Yes | ❌ No | ✅ Yes |
| **UPSCALING** | ✅ Yes (via separate API) | ❌ No | ✅ Yes (Creative Upscale) |
| **IMAGE VARIATIONS** | ✅ Yes (seed + numberResults) | ✅ Yes (multi-turn conversation) | ✅ Yes (seed + num_images) |
| **BATCH GENERATION** | ✅ Yes (1-20 images) | ✅ Yes (implied) | ✅ Yes (num_images) |
| **SEED CONTROL** | ✅ Yes (explicit seed) | ❌ No | ✅ Yes (explicit seed) |
| **ASPECT RATIO CONTROL** | ✅ Yes (custom width/height) | ✅ Yes (predefined ratios) | ✅ Yes (custom width/height) |
| **STYLE PRESETS** | ❌ No | ❌ No | ✅ Yes (styleUUID, presetStyle) |
| **MULTI-TURN EDITING** | ❌ No | ✅ Yes (conversational) | ❌ No |
| **TEXT IN IMAGES** | ⚠️ Model dependent | ✅ Yes (high-fidelity) | ⚠️ Model dependent |
| **TRANSPARENT BACKGROUNDS** | ✅ Yes (LayerDiffuse for FLUX) | ✅ Yes (request in prompt) | ❌ No |
| **PHOTOREALISTIC MODE** | ⚠️ Model dependent | ✅ Yes (model optimized) | ✅ Yes (PhotoReal v1/v2) |
| **CUSTOM MODELS** | ✅ Yes (via AIR system) | ❌ No | ✅ Yes (user-trained) |
| **REFINERS** | ✅ Yes (SDXL refiners) | ❌ No | ❌ No |
| **VAE CONTROL** | ✅ Yes | ❌ No | ❌ No |
| **SCHEDULER CONTROL** | ✅ Yes (multiple options) | ❌ No | ✅ Yes (limited) |
| **NSFW DETECTION** | ✅ Yes (optional check) | ✅ Yes (automatic, SynthID) | ⚠️ Not documented |
| **WEBHOOKS** | ✅ Yes (uploadEndpoint) | ❌ No | ✅ Yes (callback URL) |
| **PROMPT LENGTH LIMIT** | 2-3000 characters | No strict limit | Not specified |
| **IMAGE QUALITY CONTROL** | ✅ Yes (steps, CFG, quality) | ⚠️ Limited | ✅ Yes (steps, guidance_scale) |
| **PERFORMANCE ACCELERATION** | ✅ Yes (TeaCache, DeepCache) | ❌ No | ✅ Yes (Alchemy) |
| **COST TRACKING** | ✅ Yes (includeCost flag) | ✅ Yes (token-based) | ✅ Yes (API credit cost) |

---

## Table 2: Request Parameters Comparison

| Parameter | Runware | Gemini (Nano Banana) | Leonardo AI | Mapping Notes |
|-----------|---------|---------------------|-------------|---------------|
| **CORE GENERATION** |
| Prompt (positive) | `positivePrompt` (string, 2-3000 chars) | `contents` (text part in array) | `prompt` (string) | ✅ **Mappable** - all support text prompts |
| Negative Prompt | `negativePrompt` (string, 2-3000 chars) | ❌ N/A | `negative_prompt` (string) | ⚠️ **Partial** - Gemini doesn't support |
| Model ID | `model` (AIR string) | `model` (fixed: gemini-2.5-flash-image) | `modelId` (UUID string) | ⚠️ **Provider-specific** - different ID systems |
| Width | `width` (128-2048, div by 64) | Via `aspectRatio` or default | `width` (32-1024, div by 8) | ⚠️ **Partial** - different ranges/methods |
| Height | `height` (128-2048, div by 64) | Via `aspectRatio` or default | `height` (32-1024, div by 8) | ⚠️ **Partial** - different ranges/methods |
| Number of Images | `numberResults` (1-20) | Via multiple calls or config | `num_images` (integer) | ✅ **Mappable** - similar concept |
| Seed | `seed` (1 to 9.2e18) | ❌ N/A | `seed` (integer) | ⚠️ **Partial** - Gemini doesn't support |
| **QUALITY CONTROL** |
| Inference Steps | `steps` (1-100, default: 20) | ❌ N/A (automatic) | `num_inference_steps` (integer) | ⚠️ **Partial** - Gemini automatic |
| Guidance Scale | `CFGScale` (0-50, default: 7) | ❌ N/A (automatic) | `guidance_scale` (1-20 or 2-30) | ⚠️ **Partial** - Gemini automatic |
| Scheduler | `scheduler` (string) | ❌ N/A | `scheduler` (string, limited) | ⚠️ **Provider-specific** |
| Output Quality | `outputQuality` (20-99, default: 95) | ❌ N/A | ❌ N/A | ❌ **Unique to Runware** |
| **OUTPUT FORMAT** |
| Output Type | `outputType` (URL/base64/dataURI) | Returns base64 in response | Returns URL after polling | ⚠️ **Different mechanisms** |
| Output Format | `outputFormat` (JPG/PNG/WEBP) | PNG default | PNG/JPG | ⚠️ **Partial** - different options |
| Aspect Ratio | Via width/height | `aspectRatio` (1:1, 16:9, etc.) | Via width/height | ⚠️ **Different approaches** |
| **IMAGE GUIDANCE** |
| Seed Image | `seedImage` (UUID/URL/base64/dataURI) | `contents` (inline_data in array) | `init_image_id` or `init_generation_image_id` | ⚠️ **Different formats** |
| Image Strength | `strength` (0-1, default: 0.8) | ❌ N/A (in prompt) | `init_strength` (0-1) | ⚠️ **Partial** - Gemini via prompt |
| Mask Image | `maskImage` (UUID/URL/base64/dataURI) | ❌ N/A (semantic) | Via ControlNet mask | ⚠️ **Different implementations** |
| Reference Images | `referenceImages` (array of strings) | `contents` (multiple inline_data) | Via `controlnets` array | ⚠️ **Different structures** |
| Image Prompts | ❌ N/A | `contents` (mixed text/image) | `imagePrompts` (array of IDs) | ⚠️ **Unique implementations** |
| **ADVANCED FEATURES** |
| ControlNet | `controlNet` (array of objects) | ❌ N/A | `controlnets` (array of objects) | ⚠️ **Partial** - Gemini N/A |
| LoRA | `lora` (array with model/weight) | ❌ N/A | ❌ N/A (use Elements) | ❌ **Unique to Runware** |
| Embeddings | `embeddings` (array with model/weight) | ❌ N/A | ❌ N/A | ❌ **Unique to Runware** |
| IP Adapters | `ipAdapters` (array with model/guideImage) | ❌ N/A | ❌ N/A | ❌ **Unique to Runware** |
| Style Preset | ❌ N/A | ❌ N/A | `styleUUID` or `presetStyle` | ❌ **Unique to Leonardo** |
| Alchemy | ❌ N/A | ❌ N/A | `alchemy` (boolean) | ❌ **Unique to Leonardo** |
| PhotoReal | ❌ N/A | ❌ N/A | `photoReal` + `photoRealVersion` | ❌ **Unique to Leonardo** |
| Prompt Magic | ❌ N/A | ❌ N/A | `promptMagic` (boolean/version) | ❌ **Unique to Leonardo** |
| **CHARACTER/FACE FEATURES** |
| PuLID | `puLID` (object) | ❌ N/A | ❌ N/A | ❌ **Unique to Runware** |
| ACE++ | `acePlusPlus` (object) | ❌ N/A | ❌ N/A | ❌ **Unique to Runware** |
| Character Reference | ❌ N/A | Via multi-image input | Via ControlNet with preprocessorId | ⚠️ **Different approaches** |
| **OUTPAINTING** |
| Outpaint | `outpaint` (top/right/bottom/left/blur) | ❌ N/A | ❌ N/A | ❌ **Unique to Runware** |
| **REFINEMENT** |
| Refiner | `refiner` (model/startStep/startStepPercentage) | ❌ N/A | ❌ N/A | ❌ **Unique to Runware** |
| VAE | `vae` (AIR string) | ❌ N/A | ❌ N/A | ❌ **Unique to Runware** |
| **PROMPT WEIGHTING** |
| Prompt Weighting | `promptWeighting` (compel/sdEmbeds) | ❌ N/A | ❌ N/A | ❌ **Unique to Runware** |
| Clip Skip | `clipSkip` (0-2) | ❌ N/A | ❌ N/A | ❌ **Unique to Runware** |
| **PERFORMANCE** |
| Accelerator Options | `acceleratorOptions` (TeaCache/DeepCache) | ❌ N/A | Alchemy provides optimization | ⚠️ **Different implementations** |
| High Contrast | ❌ N/A | ❌ N/A | `highContrast` (boolean) | ❌ **Unique to Leonardo** |
| High Resolution | ❌ N/A | ❌ N/A | `highResolution` (boolean) | ❌ **Unique to Leonardo** |
| Contrast | ❌ N/A | ❌ N/A | `contrast` (1.0-4.5) | ❌ **Unique to Leonardo** |
| Ultra Mode | ❌ N/A | ❌ N/A | `ultra` (boolean) | ❌ **Unique to Leonardo** |
| **METADATA & TRACKING** |
| Task UUID | `taskUUID` (UUID v4, required) | ❌ N/A | ❌ N/A (returns generationId) | ⚠️ **Different tracking** |
| Check NSFW | `checkNSFW` (boolean) | Automatic (SynthID watermark) | ❌ Not documented | ⚠️ **Different approaches** |
| Include Cost | `includeCost` (boolean) | Token-based (always included) | Returns apiCreditCost | ⚠️ **Different methods** |
| Upload Endpoint | `uploadEndpoint` (webhook URL) | ❌ N/A | Webhook via API key setup | ⚠️ **Different webhook impl** |
| **PROVIDER-SPECIFIC** |
| Provider Settings | `providerSettings.bfl.*` | ❌ N/A | ❌ N/A | ❌ **Runware-specific** |
| Response Modalities | ❌ N/A | `responseModalities` (Text/Image) | ❌ N/A | ❌ **Gemini-specific** |
| Image Config | ❌ N/A | `imageConfig.aspectRatio` | ❌ N/A | ❌ **Gemini-specific** |
| Enhance Prompt | ❌ N/A | ❌ N/A | `enhancePrompt` + `enhancePromptInstruction` | ❌ **Leonardo-specific** |
| Tiling | ❌ N/A | ❌ N/A | `tiling` (boolean) | ❌ **Leonardo-specific** |
| Public | ❌ N/A | ❌ N/A | `public` (boolean) | ❌ **Leonardo-specific** |

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

---

## Recommended Implementation Strategy

### Common Abstraction Layer

Create a unified interface that handles the different mechanisms:

```typescript
interface ImageGenerationService {
  // Common interface
  generate(params: CommonImageParams): Promise<GenerationResult>
  
  // Provider-specific implementations
  // - Runware: Direct call with taskUUID
  // - Gemini: Direct call, extract base64
  // - Leonardo: POST + poll/webhook
}

interface CommonImageParams {
  prompt: string
  negativePrompt?: string
  width?: number
  height?: number
  numImages?: number
  seed?: number
  // ... map other common parameters
}

interface GenerationResult {
  id: string
  images: ImageData[]
  cost?: number
  metadata: Record<string, any>
}
```

### Polling Strategy for Leonardo AI

```typescript
async function waitForGeneration(
  generationId: string,
  maxAttempts: number = 60,
  intervalMs: number = 5000
): Promise<GenerationResult> {
  for (let i = 0; i < maxAttempts; i++) {
    const status = await getGeneration(generationId)
    
    if (status.status === 'COMPLETE') {
      return mapToGenerationResult(status)
    }
    
    if (status.status === 'FAILED') {
      throw new Error('Generation failed')
    }
    
    await sleep(intervalMs)
  }
  
  throw new Error('Generation timeout')
}
```

### Webhook Implementation for Leonardo AI

For production systems, prefer webhooks over polling:

1. Set up webhook URL during API key creation
2. Implement endpoint to receive generation complete notifications
3. Store generation requests in database with status
4. Update status when webhook received

---

## Cost Comparison Notes

- **Runware**: Pay per generation, optional `includeCost` returns actual cost
- **Gemini**: Token-based pricing (~$30 per 1M tokens, 1290 tokens per image)
- **Leonardo AI**: Credit-based system, `apiCreditCost` returned with generation

---

## Conclusion

**Choose Runware if you need:**
- Maximum customization (LoRA, ControlNet, Embeddings)
- Fine-grained control over diffusion process
- Multiple output formats
- Advanced features like PuLID, outpainting, refiners

**Choose Gemini if you need:**
- Simplest integration
- Conversational/iterative refinement
- High-quality text rendering in images
- Multi-image composition
- No polling complexity

**Choose Leonardo AI if you need:**
- PhotoReal specialized models
- Preset styles for rapid results
- Non-blocking async workflow at scale
- Custom model training
- Cinematic/artistic specific outputs

**For Multi-Provider Service:**
Implement an abstraction layer with provider-specific adapters that handle:
- Parameter translation
- Generation mechanism (sync/async/polling)
- Response normalization
- Error handling and retries