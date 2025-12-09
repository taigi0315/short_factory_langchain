# [TICKET-044] Improve Vertical Image Composition

## Priority
- [ ] Critical
- [x] High
- [ ] Medium
- [ ] Low

## Type
- [ ] Bug Fix
- [ ] Refactoring
- [x] Quality Improvement

## Impact Assessment
**Business Impact**: Better visuals for YouTube Shorts/TikTok (vertical content).
**Technical Impact**: `ImageGenAgent`, `GeminiImageClient`
**Effort Estimate**: Medium (2-4 hours)

## Problem Description
Images generated for vertical videos often look like horizontal images cropped to vertical, cutting off important subjects. The current prompt engineering adds "vertical composition" keywords, but the model (Gemini 2.5 Flash) might default to squares, making cropping destructive.

## Proposed Solution
1. **Verify Native Aspect Ratio**: Check if `google.generativeai` supports a native `aspect_ratio` or `width`/`height` parameter in the API call config (besides just prompt text).
2. **Prompt Engineering**: Stronger emphasis on "central composition" and "tall framing" in the prompt.
   - e.g., "Full body shot", "Zoomed out", "Subject in center with ample headroom".
3. **Smart Cropping (Optional)**: If we must crop from square, investigate if we can use a simple "smart crop" heuristic (though this might be complex without CV).
4. **Fallback Strategy**: If native vertical generation isn't supported, generating a *wider* image (e.g., 16:9) and cropping is worse. We should generate a *square* (1:1) and accept the crop, or try to generate *vertical* if supported.

## Files Affected
- `src/agents/image_gen/agent.py` (`_enhance_prompt_text`)
- `src/agents/image_gen/gemini_image_client.py` (`generate_image`)

## Success Criteria
- [ ] Vertical videos show images where the main subject is clearly visible.
- [ ] Reduced incidences of "half-face" or "cut-off body" in generated images.
