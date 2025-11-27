import os
from typing import List, Dict
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, TextClip, ColorClip
from src.models.models import Scene, VideoScript
from src.agents.director.models import DirectedScript
from src.agents.director.agent import DirectorAgent
from src.core.config import settings
import structlog

logger = structlog.get_logger()

from src.agents.base_agent import BaseAgent

class VideoAssemblyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="VideoAssemblyAgent",
            require_llm=False
        )

    def _setup(self):
        """Agent-specific setup."""
        self.output_dir = os.path.join(settings.GENERATED_ASSETS_DIR, "videos")
        os.makedirs(self.output_dir, exist_ok=True)

    async def assemble_video(
        self, 
        script: VideoScript, 
        image_paths: Dict[int, List[str]], 
        audio_paths: Dict[int, str]
    ) -> str:
        """
        Assembles the video from images and audio.
        Returns the path to the final video file.
        """
        print("Assembling video...")
        clips = []
        
        for scene in script.scenes:
            scene_num = scene.scene_number
            
            if scene_num not in image_paths or scene_num not in audio_paths:
                print(f"Skipping scene {scene_num}: Missing assets")
                continue
                
            image_paths_list = image_paths[scene_num]
            # Handle case where image_paths might be a single string (backward compatibility)
            if isinstance(image_paths_list, str):
                image_paths_list = [image_paths_list]
                
            audio_path = audio_paths[scene_num]
            

            audio_clip = AudioFileClip(audio_path)
            total_duration = audio_clip.duration
            
            num_images = len(image_paths_list)
            image_durations = []
            
            if hasattr(scene, 'content') and scene.content and len(scene.content) == num_images:
                segment_texts = [seg.segment_text for seg in scene.content]
                image_durations = self._calculate_segment_durations(total_duration, segment_texts)
            else:
                if num_images > 0:
                    image_durations = [total_duration / num_images] * num_images
                else:
                    image_durations = [total_duration]
            
            scene_clips = []
            for i, img_path in enumerate(image_paths_list):
                if i < len(image_durations):
                    duration = image_durations[i]
                else:
                    duration = total_duration / num_images
                
                img_clip = ImageClip(img_path).with_duration(duration)
                
                effect_name = getattr(scene, 'selected_effect', 'ken_burns_zoom_in')
                img_clip = self._apply_effect(img_clip, effect_name, duration)
                
                scene_clips.append(img_clip)
            
            if len(scene_clips) > 1:
                visual_clip = concatenate_videoclips(scene_clips, method="compose")
            elif len(scene_clips) == 1:
                visual_clip = scene_clips[0]
            else:
                logger.error("No clips created for scene", scene_num=scene_num)
                continue
            
            video_clip = visual_clip.with_audio(audio_clip)
            
            clips.append(video_clip)
            
        if not clips:
            raise ValueError("No clips were created. Check asset generation.")
            
        final_video = concatenate_videoclips(clips, method="compose")
        
        # Add title overlay using PIL (more reliable than ImageMagick)
        try:
            print(f"Adding title overlay: {script.title}")
            title_clip = self._create_title_overlay(script.title, final_video.w, final_video.h)
            final_video = CompositeVideoClip([final_video, title_clip])
            logger.info("Title overlay added successfully")
        except Exception as e:
            logger.warning("Failed to add title overlay", error=str(e))
            print(f"WARNING: Could not add title overlay: {e}")
        
        # Add subtitles for each scene
        try:
            print("Adding subtitles...")
            subtitle_clips = self._create_subtitles(script, clips, final_video.w, final_video.h)
            if subtitle_clips:
                final_video = CompositeVideoClip([final_video] + subtitle_clips)
                logger.info(f"Added {len(subtitle_clips)} subtitle clips")
        except Exception as e:
            logger.warning("Failed to add subtitles", error=str(e))
            print(f"WARNING: Could not add subtitles: {e}")
        
        output_filename = f"{script.title.replace(' ', '_')}_final.mp4"
        output_path = os.path.join(self.output_dir, output_filename)
        
        print(f"Writing video to {output_path}...")
        final_video.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')
        return output_path

    async def assemble_video_from_directed_script(
        self,
        directed_script: DirectedScript,
        image_paths: Dict[int, List[str]],
        audio_paths: Dict[int, str]
    ) -> str:
        """
        Assembles video from a DirectedScript using the Director's cinematic direction.
        
        Args:
            directed_script: DirectedScript with cinematic direction
            image_paths: Dictionary mapping scene_number to list of image paths
            audio_paths: Dictionary mapping scene_number to audio path
            
        Returns:
            Path to the final video file
        """
        logger.info("Assembling video from directed script", scenes=len(directed_script.directed_scenes))
        
        director = DirectorAgent()
        
        enhanced_scenes = []
        for directed_scene in directed_script.directed_scenes:
            scene = directed_scene.original_scene
            
            effect_name = director.get_effect_name(directed_scene.direction.camera_movement)
            
            enhanced_scene = Scene(
                scene_number=scene.scene_number,
                scene_type=scene.scene_type,
                voice_tone=scene.voice_tone,
                image_style=scene.image_style,
                content=directed_scene.visual_segments if directed_scene.visual_segments else scene.content,
                elevenlabs_settings=scene.elevenlabs_settings,
                needs_animation=scene.needs_animation,
                transition_to_next=scene.transition_to_next
            )
            
            enhanced_scene.selected_effect = effect_name
            
            enhanced_scenes.append(enhanced_scene)
        
        enhanced_script = VideoScript(
            title=directed_script.original_script.title,
            overall_style=directed_script.original_script.overall_style,
            global_visual_style=directed_script.original_script.global_visual_style,
            main_character_description=directed_script.original_script.main_character_description,
            scenes=enhanced_scenes
        )
        
        return await self.assemble_video(enhanced_script, image_paths, audio_paths)

    def _apply_effect(self, clip: ImageClip, effect_name: str, duration: float) -> ImageClip:
        """
        Apply visual effect to the image clip.
        """
        w, h = clip.size
        
        # Map complex/unimplemented effects to simple zoom to avoid static images
        # and avoid "dizzying" shake effects
        if effect_name in ["shake", "handheld", "crane_up", "crane_down", "orbit", "dolly_zoom"]:
            effect_name = "ken_burns_zoom_in"
        
        if effect_name == "ken_burns_zoom_in":

            return clip.resized(lambda t: 1 + 0.3 * t / duration).with_position('center')
            
        elif effect_name == "ken_burns_zoom_out":

            return clip.resized(lambda t: 1.3 - 0.3 * t / duration).with_position('center')
            
        elif effect_name == "pan_left":
            # Pan from right to left
            # We need to zoom in slightly first to have room to pan
            zoom_factor = 1.2
            new_w = w * zoom_factor
            new_h = h * zoom_factor
            

            enlarged = clip.resized(zoom_factor)
            

            # Start: Right edge aligned (x = -(new_w - w))
            # End: Left edge aligned (x = 0)
            start_x = -(new_w - w)
            end_x = 0
            
            return enlarged.with_position(lambda t: (start_x + (end_x - start_x) * t / duration, 'center'))
            
        elif effect_name == "pan_right":
            # Pan from left to right
            zoom_factor = 1.2
            new_w = w * zoom_factor
            
            enlarged = clip.resized(zoom_factor)
            
            # Start: Left edge aligned (x = 0)
            # End: Right edge aligned (x = -(new_w - w))
            start_x = 0
            end_x = -(new_w - w)
            
            return enlarged.with_position(lambda t: (start_x + (end_x - start_x) * t / duration, 'center'))
            
        elif effect_name == "tilt_up":
             # Pan from bottom to top
            zoom_factor = 1.2
            new_h = h * zoom_factor
            
            enlarged = clip.resized(zoom_factor)
            
            # Start: Bottom edge aligned (y = -(new_h - h))
            # End: Top edge aligned (y = 0)
            start_y = -(new_h - h)
            end_y = 0
            
            return enlarged.with_position(lambda t: ('center', start_y + (end_y - start_y) * t / duration))

        elif effect_name == "tilt_down":
             # Pan from top to bottom
            zoom_factor = 1.2
            new_h = h * zoom_factor
            
            enlarged = clip.resized(zoom_factor)
            
            # Start: Top edge aligned (y = 0)
            # End: Bottom edge aligned (y = -(new_h - h))
            start_y = 0
            end_y = -(new_h - h)
            
            return enlarged.with_position(lambda t: ('center', start_y + (end_y - start_y) * t / duration))
            

        return clip

    def _calculate_segment_durations(self, total_audio_duration: float, segments: List[str]) -> List[float]:
        """
        Calculates how long each image should be displayed based on text length.
        """
        # 1. Calculate lengths
        char_counts = [len(seg) for seg in segments]
        total_chars = sum(char_counts)
        
        # Edge Case: Avoid division by zero if text is empty
        if total_chars == 0:
            return [total_audio_duration / len(segments)] * len(segments)

        durations = []
        
        # 2. Calculate Ratios
        for count in char_counts:
            ratio = count / total_chars
            duration = total_audio_duration * ratio
            durations.append(duration)
            
        return durations

    def _create_title_overlay(self, title: str, video_width: int, video_height: int):
        """
        Create a title overlay using PIL to avoid ImageMagick dependency.
        
        Args:
            title: Title text to display
            video_width: Width of the video
            video_height: Height of the video
            
        Returns:
            TextClip with title overlay
        """
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
        
        # Create image for title with transparency
        img_width = int(video_width * 0.9)
        img_height = 150
        
        # Create transparent image
        img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Try to load a font, fall back to default if needed
        try:
            # Try common system fonts
            font_size = 60
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except:
                # Fall back to default font
                font = ImageFont.load_default()
        
        # Word wrap the title if too long
        words = title.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] < img_width - 40:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw text with stroke (outline)
        y_offset = 20
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (img_width - text_width) // 2
            
            # Draw black outline
            for adj_x in range(-2, 3):
                for adj_y in range(-2, 3):
                    draw.text((x + adj_x, y_offset + adj_y), line, font=font, fill=(0, 0, 0, 255))
            
            # Draw white text
            draw.text((x, y_offset), line, font=font, fill=(255, 255, 255, 255))
            y_offset += bbox[3] - bbox[1] + 10
        
        # Convert PIL image to numpy array for MoviePy
        img_array = np.array(img)
        
        # Create ImageClip from numpy array
        from moviepy import ImageClip
        title_clip = ImageClip(img_array, duration=3)
        title_clip = title_clip.with_position(('center', 50))
        
        return title_clip

    def _create_subtitles(self, script: VideoScript, scene_clips: List, video_width: int, video_height: int):
        """
        Create subtitle overlays for each scene based on dialogue segments.
        
        Args:
            script: VideoScript with scene information
            scene_clips: List of video clips for each scene
            video_width: Width of the video
            video_height: Height of the video
            
        Returns:
            List of TextClip objects for subtitles
        """
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
        
        subtitle_clips = []
        current_time = 0.0
        
        # Skip first 3 seconds (title overlay duration)
        current_time = 3.0
        
        for i, scene in enumerate(script.scenes):
            if i >= len(scene_clips):
                break
                
            scene_clip = scene_clips[i]
            scene_duration = scene_clip.duration
            
            # Get subtitle text from scene content
            if hasattr(scene, 'content') and scene.content:
                # Multiple segments per scene
                segment_texts = [seg.segment_text for seg in scene.content if seg.segment_text]
                
                if segment_texts:
                    # Calculate duration for each segment
                    segment_duration = scene_duration / len(segment_texts)
                    
                    for seg_text in segment_texts:
                        if seg_text.strip():
                            subtitle_clip = self._create_subtitle_clip(
                                seg_text, 
                                video_width, 
                                video_height,
                                start_time=current_time,
                                duration=segment_duration
                            )
                            subtitle_clips.append(subtitle_clip)
                            current_time += segment_duration
                else:
                    # No segment text, skip
                    current_time += scene_duration
            else:
                # No content, skip
                current_time += scene_duration
        
        return subtitle_clips

    def _create_subtitle_clip(self, text: str, video_width: int, video_height: int, start_time: float, duration: float):
        """
        Create a single subtitle clip using PIL.
        
        Args:
            text: Subtitle text
            video_width: Width of the video
            video_height: Height of the video
            start_time: When subtitle should appear
            duration: How long subtitle should display
            
        Returns:
            ImageClip with subtitle
        """
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
        
        # Create image for subtitle
        img_width = int(video_width * 0.9)
        img_height = 120
        
        img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Load font
        try:
            font_size = 40
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        # Word wrap
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] < img_width - 40:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Limit to 2 lines
        lines = lines[:2]
        
        # Draw text with background
        y_offset = 10
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (img_width - text_width) // 2
            
            # Draw semi-transparent black background
            padding = 10
            draw.rectangle(
                [x - padding, y_offset - padding, x + text_width + padding, y_offset + text_height + padding],
                fill=(0, 0, 0, 180)
            )
            
            # Draw white text
            draw.text((x, y_offset), line, font=font, fill=(255, 255, 255, 255))
            y_offset += text_height + 5
        
        # Convert to numpy array
        img_array = np.array(img)
        
        # Create ImageClip
        from moviepy import ImageClip
        subtitle_clip = ImageClip(img_array, duration=duration)
        subtitle_clip = subtitle_clip.with_position(('center', video_height - 200))
        subtitle_clip = subtitle_clip.with_start(start_time)
        
        return subtitle_clip

