"""
Cinematic Language Library

Defines shot types, camera movements, angles, lighting, and composition rules
for the Director Agent to use in creating visually coherent video narratives.
"""

from enum import Enum
from typing import Dict, List

# Shot Types
class ShotType(str, Enum):
    """Types of camera shots and their purposes"""
    EXTREME_WIDE = "extreme_wide"
    WIDE = "wide"
    MEDIUM = "medium"
    MEDIUM_CLOSE_UP = "medium_close_up"
    CLOSE_UP = "close_up"
    EXTREME_CLOSE_UP = "extreme_close_up"

SHOT_TYPE_GUIDE = {
    ShotType.EXTREME_WIDE: {
        "purpose": "Establish location, show scale and context",
        "emotional_impact": "Isolation, grandeur, overwhelming scope",
        "when_to_use": ["Opening shots", "Location changes", "Scope reveals"],
        "framing": "Character is tiny in frame, environment dominates"
    },
    ShotType.WIDE: {
        "purpose": "Show full scene, character in environment",
        "emotional_impact": "Context, spatial relationships, freedom",
        "when_to_use": ["Scene establishment", "Action sequences", "Group dynamics"],
        "framing": "Full body visible, environment clearly shown"
    },
    ShotType.MEDIUM: {
        "purpose": "Character interaction, dialogue, body language",
        "emotional_impact": "Connection, conversation, comfort",
        "when_to_use": ["Dialogue scenes", "Explanations", "Character interactions"],
        "framing": "Waist up, balanced character and environment"
    },
    ShotType.MEDIUM_CLOSE_UP: {
        "purpose": "Focus on character while maintaining some context",
        "emotional_impact": "Intimacy with awareness, personal connection",
        "when_to_use": ["Important dialogue", "Emotional moments", "Reactions"],
        "framing": "Chest up, face is primary focus"
    },
    ShotType.CLOSE_UP: {
        "purpose": "Capture emotion, detail, intimacy",
        "emotional_impact": "Intensity, focus, emotional connection",
        "when_to_use": ["Emotional peaks", "Reveals", "Emphasis moments"],
        "framing": "Face fills frame, eyes are key"
    },
    ShotType.EXTREME_CLOSE_UP: {
        "purpose": "Extreme detail, maximum tension",
        "emotional_impact": "Anxiety, hyper-focus, revelation",
        "when_to_use": ["Critical discoveries", "Horror", "Intense emotion"],
        "framing": "Eyes, mouth, or specific detail fills entire frame"
    }
}

# Camera Movements
class CameraMovement(str, Enum):
    """Types of camera movements"""
    STATIC = "static"
    SLOW_PUSH_IN = "slow_push_in"
    FAST_PUSH_IN = "fast_push_in"
    PULL_BACK = "pull_back"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    TILT_UP = "tilt_up"
    TILT_DOWN = "tilt_down"
    DOLLY_ZOOM = "dolly_zoom"
    CRANE_UP = "crane_up"
    CRANE_DOWN = "crane_down"
    HANDHELD = "handheld"
    ORBIT = "orbit"

CAMERA_MOVEMENT_GUIDE = {
    CameraMovement.STATIC: {
        "effect": "Stability, observation, clarity",
        "emotion": "Calm, focused, contemplative",
        "when_to_use": ["Information delivery", "Stable moments", "Observation"]
    },
    CameraMovement.SLOW_PUSH_IN: {
        "effect": "Building tension, increasing focus, drawing viewer in",
        "emotion": "Intrigue, intimacy, building intensity",
        "when_to_use": ["Mystery reveals", "Emotional builds", "Focus shifts"]
    },
    CameraMovement.FAST_PUSH_IN: {
        "effect": "Sudden emphasis, shock, urgency",
        "emotion": "Surprise, alarm, realization",
        "when_to_use": ["Shocking reveals", "Sudden realizations", "Impact moments"]
    },
    CameraMovement.PULL_BACK: {
        "effect": "Revelation of context, perspective shift, distancing",
        "emotion": "Understanding, perspective, sometimes isolation",
        "when_to_use": ["Context reveals", "Endings", "Perspective shifts"]
    },
    CameraMovement.PAN_LEFT: {
        "effect": "Discovery, exploration, following action",
        "emotion": "Curiosity, progression, exploration",
        "when_to_use": ["Revealing new elements", "Following movement", "Exploration"]
    },
    CameraMovement.PAN_RIGHT: {
        "effect": "Continuation, progression, time passage",
        "emotion": "Forward movement, discovery, continuation",
        "when_to_use": ["Progression", "Time passage", "Discovery"]
    },
    CameraMovement.TILT_UP: {
        "effect": "Awe, grandeur, hope, aspiration",
        "emotion": "Wonder, hope, reverence, power",
        "when_to_use": ["Revealing height", "Moments of awe", "Hopeful moments"]
    },
    CameraMovement.TILT_DOWN: {
        "effect": "Grounding, detail focus, sometimes despair",
        "emotion": "Focus, grounding, sometimes sadness",
        "when_to_use": ["Detail reveals", "Grounding moments", "Downward emotional shifts"]
    },
    CameraMovement.DOLLY_ZOOM: {
        "effect": "Disorientation, vertigo, realization",
        "emotion": "Shock, realization, unease",
        "when_to_use": ["Major revelations", "Disorienting moments", "Vertigo effects"]
    },
    CameraMovement.CRANE_UP: {
        "effect": "Freedom, escape, god's eye view",
        "emotion": "Liberation, overview, transcendence",
        "when_to_use": ["Endings", "Escape moments", "Overview shots"]
    },
    CameraMovement.HANDHELD: {
        "effect": "Urgency, chaos, realism, immediacy",
        "emotion": "Tension, urgency, authenticity",
        "when_to_use": ["Action", "Chaos", "Documentary feel"]
    }
}

# Camera Angles
class CameraAngle(str, Enum):
    """Camera angle relative to subject"""
    EYE_LEVEL = "eye_level"
    LOW = "low"
    HIGH = "high"
    DUTCH = "dutch"
    OVERHEAD = "overhead"

CAMERA_ANGLE_GUIDE = {
    CameraAngle.EYE_LEVEL: {
        "effect": "Neutral, relatable, natural",
        "emotion": "Equality, normalcy, comfort",
        "when_to_use": ["Standard dialogue", "Neutral moments", "Relatability"]
    },
    CameraAngle.LOW: {
        "effect": "Power, dominance, intimidation, heroism",
        "emotion": "Awe, fear, respect, power",
        "when_to_use": ["Powerful moments", "Hero shots", "Intimidation"]
    },
    CameraAngle.HIGH: {
        "effect": "Vulnerability, weakness, overview",
        "emotion": "Vulnerability, insignificance, observation",
        "when_to_use": ["Vulnerable moments", "Establishing context", "Weakness"]
    },
    CameraAngle.DUTCH: {
        "effect": "Unease, disorientation, wrongness",
        "emotion": "Unease, chaos, instability",
        "when_to_use": ["Disorienting moments", "Chaos", "Psychological tension"]
    },
    CameraAngle.OVERHEAD: {
        "effect": "God's eye view, isolation, pattern",
        "emotion": "Detachment, pattern recognition, isolation",
        "when_to_use": ["Establishing patterns", "Isolation", "Unique perspectives"]
    }
}

# Lighting Moods
class LightingMood(str, Enum):
    """Lighting styles and moods"""
    BRIGHT = "bright"
    DRAMATIC = "dramatic"
    SOFT = "soft"
    HARSH = "harsh"
    GOLDEN_HOUR = "golden_hour"
    BLUE_HOUR = "blue_hour"
    SILHOUETTE = "silhouette"
    CHIAROSCURO = "chiaroscuro"

LIGHTING_MOOD_GUIDE = {
    LightingMood.BRIGHT: {
        "description": "High key, even lighting, minimal shadows",
        "emotion": "Happiness, clarity, openness, optimism",
        "when_to_use": ["Happy moments", "Clear explanations", "Positive scenes"]
    },
    LightingMood.DRAMATIC: {
        "description": "Strong contrasts, deep shadows, directional light",
        "emotion": "Tension, mystery, intensity, drama",
        "when_to_use": ["Dramatic moments", "Tension", "Mystery"]
    },
    LightingMood.SOFT: {
        "description": "Diffused, gentle, flattering light",
        "emotion": "Calm, gentle, romantic, peaceful",
        "when_to_use": ["Calm moments", "Romance", "Gentle scenes"]
    },
    LightingMood.HARSH: {
        "description": "Hard, unflattering, stark shadows",
        "emotion": "Harshness, reality, discomfort, truth",
        "when_to_use": ["Harsh truths", "Uncomfortable moments", "Reality"]
    },
    LightingMood.GOLDEN_HOUR: {
        "description": "Warm, golden, magical quality",
        "emotion": "Nostalgia, warmth, magic, beauty",
        "when_to_use": ["Beautiful moments", "Nostalgia", "Magic"]
    },
    LightingMood.SILHOUETTE: {
        "description": "Backlit, shape only, no detail",
        "emotion": "Mystery, anonymity, dramatic emphasis",
        "when_to_use": ["Mystery", "Dramatic reveals", "Anonymity"]
    },
    LightingMood.CHIAROSCURO: {
        "description": "Extreme contrast, artistic shadows",
        "emotion": "Drama, artistry, depth, complexity",
        "when_to_use": ["Artistic moments", "Complexity", "Depth"]
    }
}

# Composition Rules
class CompositionRule(str, Enum):
    """Composition and framing rules"""
    RULE_OF_THIRDS = "rule_of_thirds"
    CENTERED = "centered"
    SYMMETRY = "symmetry"
    LEADING_LINES = "leading_lines"
    FRAME_WITHIN_FRAME = "frame_within_frame"
    NEGATIVE_SPACE = "negative_space"
    DIAGONAL = "diagonal"

COMPOSITION_GUIDE = {
    CompositionRule.RULE_OF_THIRDS: {
        "description": "Subject on intersection of thirds grid",
        "effect": "Natural, balanced, professional",
        "when_to_use": ["Most scenes", "Natural composition", "Balance"]
    },
    CompositionRule.CENTERED: {
        "description": "Subject dead center in frame",
        "effect": "Formal, powerful, direct",
        "when_to_use": ["Powerful moments", "Direct address", "Symmetry"]
    },
    CompositionRule.SYMMETRY: {
        "description": "Balanced, mirrored composition",
        "effect": "Harmony, perfection, sometimes unease",
        "when_to_use": ["Perfection", "Harmony", "Wes Anderson style"]
    },
    CompositionRule.LEADING_LINES: {
        "description": "Lines guide eye to subject",
        "effect": "Direction, focus, depth",
        "when_to_use": ["Guiding attention", "Depth", "Direction"]
    },
    CompositionRule.FRAME_WITHIN_FRAME: {
        "description": "Natural frames around subject",
        "effect": "Focus, depth, context",
        "when_to_use": ["Focus emphasis", "Depth", "Isolation"]
    },
    CompositionRule.NEGATIVE_SPACE: {
        "description": "Empty space around subject",
        "effect": "Isolation, emphasis, breathing room",
        "when_to_use": ["Isolation", "Minimalism", "Emphasis"]
    },
    CompositionRule.DIAGONAL: {
        "description": "Diagonal lines create energy",
        "effect": "Dynamic, energy, movement",
        "when_to_use": ["Action", "Energy", "Dynamic scenes"]
    }
}

# Visual Continuity Rules
VISUAL_CONTINUITY_RULES = {
    "match_on_action": {
        "rule": "Cut during movement for seamless flow",
        "example": "Character starts pointing in shot 1, completes point in shot 2"
    },
    "eyeline_match": {
        "rule": "Follow character's gaze to next shot",
        "example": "Character looks off-screen, cut to what they're seeing"
    },
    "graphic_match": {
        "rule": "Similar compositions for smooth transition",
        "example": "Circular object in shot 1 matches circular object in shot 2"
    },
    "180_degree_rule": {
        "rule": "Maintain spatial relationships across cuts",
        "example": "Keep camera on same side of action line"
    },
    "30_degree_rule": {
        "rule": "Change angle enough to avoid jump cut",
        "example": "Move camera at least 30 degrees between shots of same subject"
    },
    "shot_progression": {
        "rule": "Vary shot sizes for visual interest",
        "example": "Wide → Medium → Close-up creates natural progression"
    }
}

# Emotional Arc Mapping
EMOTION_TO_VISUAL = {
    "mystery": {
        "shot_type": ShotType.MEDIUM_CLOSE_UP,
        "camera_movement": CameraMovement.SLOW_PUSH_IN,
        "camera_angle": CameraAngle.LOW,
        "lighting": LightingMood.DRAMATIC,
        "composition": CompositionRule.NEGATIVE_SPACE
    },
    "revelation": {
        "shot_type": ShotType.CLOSE_UP,
        "camera_movement": CameraMovement.FAST_PUSH_IN,
        "camera_angle": CameraAngle.EYE_LEVEL,
        "lighting": LightingMood.BRIGHT,
        "composition": CompositionRule.CENTERED
    },
    "triumph": {
        "shot_type": ShotType.WIDE,
        "camera_movement": CameraMovement.CRANE_UP,
        "camera_angle": CameraAngle.LOW,
        "lighting": LightingMood.GOLDEN_HOUR,
        "composition": CompositionRule.SYMMETRY
    },
    "sadness": {
        "shot_type": ShotType.CLOSE_UP,
        "camera_movement": CameraMovement.STATIC,
        "camera_angle": CameraAngle.HIGH,
        "lighting": LightingMood.SOFT,
        "composition": CompositionRule.NEGATIVE_SPACE
    },
    "excitement": {
        "shot_type": ShotType.MEDIUM,
        "camera_movement": CameraMovement.HANDHELD,
        "camera_angle": CameraAngle.EYE_LEVEL,
        "lighting": LightingMood.BRIGHT,
        "composition": CompositionRule.DIAGONAL
    },
    "calm": {
        "shot_type": ShotType.WIDE,
        "camera_movement": CameraMovement.STATIC,
        "camera_angle": CameraAngle.EYE_LEVEL,
        "lighting": LightingMood.SOFT,
        "composition": CompositionRule.SYMMETRY
    }
}
