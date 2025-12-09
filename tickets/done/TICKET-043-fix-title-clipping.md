# [TICKET-043] Fix Title/Subtitle Clipping and Font Issues

## Priority
- [ ] Critical
- [x] High
- [ ] Medium
- [ ] Low

## Type
- [x] Bug Fix
- [ ] Refactoring
- [ ] Feature

## Impact Assessment
**Business Impact**: Prevents "amateur" look of video titles being cut off.
**Technical Impact**: `VideoGenAgent`
**Effort Estimate**: Small (1-2 hours)

## Problem Description
The user reported that long titles are being cut off at the sides and top of the video in vertical (9:16) mode. The current implementation uses a fixed percentage of screen height for font size, which doesn't account for title length.

## Proposed Solution
1. **Dynamic Font Sizing**: Implement a "shrink-to-fit" or adaptive font size calculation. Start with a target size but reduce it if the text width exceeds the safe margin.
2. **Safe Margins**: Increase standard side margins (currently 85% width -> maybe 80%) to ensure text doesn't touch edges.
3. **Font Loading**: Ensure a fallback to a decent font if system fonts aren't found (avoid `ImageFont.load_default()` which is tiny/ugly).
4. **Positioning**: Adjust vertical centering or top padding to ensure it doesn't overlap excessively with the image header space.

## Files Affected
- `src/agents/video_gen/agent.py` (`_create_title_card`, `_create_text_overlay_pil`, `_wrap_text`)

## Success Criteria
- [ ] Long titles are effectively wrapped or resized to fit within the screen width.
- [ ] Text does not touch the edges of the video (good padding).
- [ ] Subtitles (if handled similarly) are also legible and safe-zoned.
