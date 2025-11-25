"""
Centralized mock/fallback data for verification platform.
Used when LLM APIs are unavailable or keys are missing.
"""
from typing import List
from src.api.schemas.stories import StoryIdeaResponse, StoryGenerationRequest
from src.api.schemas.scripts import ScriptGenerationResponse, ScriptGenerationRequest
from src.models.models import VideoScript, Scene, SceneType, VoiceTone, ImageStyle, TransitionType, HookTechnique, ElevenLabsSettings, VisualSegment


def get_mock_stories(request: StoryGenerationRequest) -> List[StoryIdeaResponse]:
    """Returns mock story ideas for testing/demo."""
    return [
        StoryIdeaResponse(
            title=f"Mock Story 1: The {request.category} {request.topic}",
            premise=f"A {request.mood} story about {request.topic}.",
            genre=request.category,
            target_audience="General Audience",
            estimated_duration="30s"
        ),
        StoryIdeaResponse(
            title=f"Mock Story 2: {request.topic} Chronicles",
            premise=f"An exploration of {request.topic} in an unexpected way.",
            genre=request.category,
            target_audience="Curious Minds",
            estimated_duration="45s"
        ),
        StoryIdeaResponse(
            title=f"Mock Story 3: The Secret of {request.topic}",
            premise=f"Uncover the hidden truth about {request.topic}.",
            genre="Documentary",
            target_audience="Knowledge Seekers",
            estimated_duration="60s"
        )
    ]


def get_mock_script(request: ScriptGenerationRequest) -> ScriptGenerationResponse:
    """Returns mock video script for testing/demo."""
    mock_scenes = [
        Scene(
            scene_number=1,
            scene_type=SceneType.HOOK,
            content=[
                VisualSegment(
                    segment_text=f"Welcome to the amazing world of {request.story_title}!",
                    image_prompt=f"Cinematic opening shot related to {request.story_title}, dramatic lighting"
                )
            ],
            voice_tone=VoiceTone.EXCITED,
            elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.EXCITED),
            image_style=ImageStyle.CINEMATIC,
            character_pose="welcoming gesture",
            background_description="Engaging visual environment",
            needs_animation=True,
            video_prompt="Camera zooms in with dynamic movement",
            transition_to_next=TransitionType.ZOOM_IN,
            hook_technique=HookTechnique.INTRIGUING_QUESTION
        ),
        Scene(
            scene_number=2,
            scene_type=SceneType.EXPLANATION,
            content=[
                VisualSegment(
                    segment_text=f"Let me explain the key concepts of {request.story_premise}.",
                    image_prompt=f"Friendly character explaining {request.story_premise}, warm colors"
                )
            ],
            voice_tone=VoiceTone.FRIENDLY,
            elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.FRIENDLY),
            image_style=ImageStyle.CHARACTER_WITH_BACKGROUND,
            character_pose="explaining gestures",
            background_description="Comfortable setting",
            needs_animation=False,
            transition_to_next=TransitionType.FADE,
            hook_technique=None
        ),
        Scene(
            scene_number=3,
            scene_type=SceneType.VISUAL_DEMO,
            content=[
                VisualSegment(
                    segment_text="Here's how it works in practice.",
                    image_prompt="Visual demonstration with diagrams and examples"
                )
            ],
            voice_tone=VoiceTone.CURIOUS,
            elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CURIOUS),
            image_style=ImageStyle.DIAGRAM_EXPLANATION,
            character_pose="pointing at diagram",
            background_description="Educational environment",
            needs_animation=False,
            transition_to_next=TransitionType.SLIDE_LEFT,
            hook_technique=None
        ),
        Scene(
            scene_number=4,
            scene_type=SceneType.CONCLUSION,
            content=[
                VisualSegment(
                    segment_text="And that's the complete story!",
                    image_prompt="Satisfying conclusion shot with character smiling"
                )
            ],
            voice_tone=VoiceTone.CONFIDENT,
            elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CONFIDENT),
            image_style=ImageStyle.CINEMATIC,
            character_pose="confident stance",
            background_description="Uplifting environment",
            needs_animation=False,
            transition_to_next=TransitionType.FADE,
            hook_technique=None
        )
    ]
    
    return ScriptGenerationResponse(
        script=VideoScript(
            title=request.story_title,
            main_character_description=f"Character representing {request.story_audience}",
            overall_style=request.story_genre,
            global_visual_style="Mock Visual Style (e.g. 3D Pixar)",
            scenes=mock_scenes
        )
    )
