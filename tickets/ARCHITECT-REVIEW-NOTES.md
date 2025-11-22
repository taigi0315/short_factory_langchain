# Architect Review Notes - 2025-11-22

## System Understanding
### Architecture Overview
- **High-level system architecture summary**: ShortFactory is an AI-driven video generation platform that uses a multi-agent system (LangChain) to orchestrate script writing, image generation (Gemini), voice synthesis (ElevenLabs), and video assembly (MoviePy).
- **Key components**:
    - `ScriptWriterAgent`: Generates structured video scripts (JSON).
    - `ImageGenAgent`: Generates images using Gemini Imagen 3.
    - `VoiceAgent`: Generates audio using ElevenLabs or gTTS.
    - `VideoGenAgent`: Assembles assets into MP4 using MoviePy.
    - `FastAPI Backend`: Exposes endpoints for the frontend.
    - `Next.js Frontend`: User interface for generating and viewing videos.
- **Critical workflows**:
    1. User submits topic -> Script generation.
    2. Script approval -> Parallel image & audio generation.
    3. Asset collection -> Video assembly (rendering).

### Current State Assessment
**Strengths:**
- Modular agent design allows for easy swapping of components (e.g., switching LLMs or Voice providers).
- Strong typing with Pydantic models ensures data integrity between agents.
- Recent improvements in error handling (global exception handlers) and configuration (scene counts) have stabilized the core loop.

**Known Issues:**
- **Video Assembly Logic**: Currently simplistic (Ken Burns effect only), lacks precise audio sync (addressed by TICKET-016).
- **Audio Quality**: Default settings are "robotic" (addressed by TICKET-017).
- **Visual Consistency**: Aspect ratios are not enforced (addressed by TICKET-018).
- **Performance**: Video generation is slow (30s-5m), requiring long timeouts.

**Architectural Goals:**
- **Premium Quality**: Move from "slideshow" feel to "dynamic video" feel (AI video, better sync).
- **Scalability**: Optimize rendering pipeline and manage API costs.
- **Reliability**: Ensure zero failed generations due to timeouts or parsing errors.

### Technical Constraints
- **Performance requirements**: Video generation must complete within reasonable time (target < 3 mins for short videos).
- **Scalability targets**: Support concurrent generation requests (currently limited by local rendering).
- **Integration dependencies**: Gemini API (Images/Text), ElevenLabs (Audio), Future Video API (Runway/Pika).

---
## Ticket Review Process Starting Below
- Reviewed TICKET-016: Video Assembly & Audio Sync
- Reviewed TICKET-017: Audio Quality
- Reviewed TICKET-018: Image Aspect Ratio
- Reviewed TICKET-019: AI Video Generation
- Reviewed TICKET-020: Script Prompt Enhancement
