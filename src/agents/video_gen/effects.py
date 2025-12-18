"""
Video effects and camera movements for VideoGenAgent.

Provides cinematic effects like Ken Burns, pan, tilt, zoom, and more.
"""
import random
import structlog
from typing import Tuple
from moviepy import VideoClip

logger = structlog.get_logger()


class VideoEffects:
    """Handles all video effects and camera movements."""

    @staticmethod
    def apply_ken_burns(clip: VideoClip, duration: float) -> VideoClip:
        """Apply Ken Burns effect (slow zoom).

        Args:
            clip: Video clip to apply effect to
            duration: Duration of the clip in seconds

        Returns:
            Clip with Ken Burns effect applied
        """
        return clip.resized(lambda t: 1 + 0.1 * t / duration)

    @staticmethod
    def apply_effect(clip: VideoClip, effect: str, duration: float) -> VideoClip:
        """Apply the specified effect to a video clip.

        Args:
            clip: The video clip to apply effect to
            effect: Effect name (ken_burns_zoom_in, pan_left, tilt_up, etc.)
            duration: Duration of the clip in seconds

        Returns:
            Clip with effect applied
        """
        if effect == "ken_burns_zoom_in":
            return clip.resized(lambda t: 1 + 0.2 * t / duration)

        elif effect == "ken_burns_zoom_out":
            return clip.resized(lambda t: 1.2 - 0.2 * t / duration)

        elif effect == "pan_left":
            return clip.with_position(lambda t: (-100 * t / duration, 0))

        elif effect == "pan_right":
            return clip.with_position(lambda t: (100 * t / duration, 0))

        elif effect == "tilt_up":
            return clip.with_position(lambda t: (0, -100 * t / duration))

        elif effect == "tilt_down":
            return clip.with_position(lambda t: (0, 100 * t / duration))

        elif effect == "shake":
            def shake_pos(t: float) -> Tuple[int, int]:
                x = random.randint(-10, 10)
                y = random.randint(-10, 10)
                return (x, y)
            return clip.with_position(shake_pos)

        elif effect == "dolly_zoom":
            return clip.resized(lambda t: 1 + 0.3 * t / duration)

        elif effect == "crane_up":
            def crane_transform(t: float) -> float:
                scale = 1.1 - 0.1 * t / duration
                return scale
            return clip.resized(crane_transform).with_position(lambda t: (0, -50 * t / duration))

        elif effect == "crane_down":
            return clip.resized(lambda t: 1 + 0.1 * t / duration).with_position(lambda t: (0, 50 * t / duration))

        elif effect == "orbit":
            return clip.rotated(lambda t: 5 * t / duration)

        elif effect == "static" or effect == "none":
            return clip

        else:
            logger.warning(f"Unknown effect '{effect}', using static")
            return clip
