"""
Image Generation Prompt Optimization Instructions

OBJECTIVE: Optimize image generation prompts to be under 3000 characters while preserving maximum conceptual value and visual impact.

CORE PRINCIPLES:
1. Maintain artistic intent and visual concepts
2. Preserve key descriptive elements
3. Remove redundancy without losing meaning
4. Prioritize quality-enhancing terms
5. Keep style and technical specifications

OPTIMIZATION STRATEGY:

HIGH PRIORITY (Always Preserve):
- Main subject and key objects
- Art style and medium (photorealistic, digital art, oil painting, etc.)
- Lighting conditions (dramatic lighting, golden hour, soft light)
- Composition elements (close-up, wide shot, rule of thirds)
- Quality enhancers (highly detailed, masterpiece, best quality, 8k)
- Technical specifications (aspect ratio, camera settings if specified)

MEDIUM PRIORITY (Preserve When Possible):
- Color palette and mood
- Background elements
- Secondary objects
- Atmospheric conditions
- Artistic influences or references

LOW PRIORITY (Remove If Needed):
- Repetitive adjectives
- Redundant quality terms
- Excessive technical jargon
- Over-detailed background descriptions
- Multiple similar style references

OPTIMIZATION TECHNIQUES:

1. CONSOLIDATE SYNONYMS:
   - "beautiful, gorgeous, stunning" → "beautiful"
   - "highly detailed, intricate details, fine detail" → "highly detailed"
   - "masterpiece, best quality, high quality" → "masterpiece"

2. MERGE RELATED CONCEPTS:
   - "golden hour lighting, warm sunset light" → "golden hour lighting"
   - "digital art, digital painting, digital illustration" → "digital art"

3. PRIORITIZE IMPACT WORDS:
   - Keep: "dramatic", "ethereal", "cinematic", "photorealistic"
   - Remove: "nice", "good", "pleasant" (weak descriptors)

4. TECHNICAL EFFICIENCY:
   - "shot with Canon EOS R5, 85mm lens, f/1.4" → "85mm, f/1.4"
   - "ultra high resolution 8k 4k" → "8k resolution"

5. STRUCTURAL OPTIMIZATION:
   - Lead with main subject
   - Group related elements
   - End with technical/quality terms

RESPONSE FORMAT:
Return ONLY the optimized prompt without explanations, quotes, or additional text.
The optimized prompt must be under 3000 characters.
Preserve the original creative intent while maximizing efficiency.

EXAMPLE:
Input: "A stunningly beautiful, gorgeously detailed, highly intricate, masterful piece of digital art showing a breathtakingly gorgeous woman with long flowing hair..."
Output: "Masterful digital art, beautiful woman with flowing hair..."

Remember: Every character counts. Make each word contribute to the visual impact.