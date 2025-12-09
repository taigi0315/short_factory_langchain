"""
Unit tests for VideoAssemblyAgent.

Tests video assembly functionality including:
- Agent initialization
- Segment duration calculation
- Effect application
"""
import pytest
import os
from unittest.mock import MagicMock, patch
from pathlib import Path
from src.agents.video_assembly.agent import VideoAssemblyAgent
from src.models.models import Scene, SceneType, VoiceTone, ImageStyle, TransitionType, ElevenLabsSettings, VideoScript, VisualSegment


class TestVideoAssemblyAgent:
    """Test suite for VideoAssemblyAgent."""
    
    @pytest.fixture
    def agent(self):
        """Create VideoAssemblyAgent instance for testing."""
        return VideoAssemblyAgent()
    
    def test_initialization(self, agent):
        """Test agent initializes with correct settings."""
        assert agent.agent_name == "VideoAssemblyAgent"
        assert agent.output_dir is not None
        assert "videos" in str(agent.output_dir)
        assert isinstance(agent.mock_mode, bool)
    
    def test_calculate_segment_durations_equal_length(self, agent):
        """Test duration calculation for segments of equal length."""
        total_duration = 10.0
        segments = ["Text one", "Text two", "Text thr"]  # Equal length
        
        durations = agent._calculate_segment_durations(total_duration, segments)
        
        assert len(durations) == 3
        assert sum(durations) == pytest.approx(total_duration, rel=0.01)
    
    def test_calculate_segment_durations_different_lengths(self, agent):
        """Test duration calculation for segments of different lengths."""
        total_duration = 10.0
        segments = ["Short", "This is a much longer segment with more words", "Medium"]
        
        durations = agent._calculate_segment_durations(total_duration, segments)
        
        assert len(durations) == 3
        assert sum(durations) == pytest.approx(total_duration, rel=0.01)
        # Longer segment should get more time
        assert durations[1] > durations[0]
        assert durations[1] > durations[2]
    
    def test_calculate_segment_durations_single_segment(self, agent):
        """Test duration calculation for single segment."""
        total_duration = 5.0
        segments = ["Only one segment"]
        
        durations = agent._calculate_segment_durations(total_duration, segments)
        
        assert len(durations) == 1
        assert durations[0] == pytest.approx(total_duration)
    
    def test_calculate_segment_durations_empty_segments(self, agent):
        """Test duration calculation handles empty segments."""
        total_duration = 10.0
        segments = ["Text", "", "More text"]
        
        durations = agent._calculate_segment_durations(total_duration, segments)
        
        assert len(durations) == 3
        assert sum(durations) == pytest.approx(total_duration, rel=0.01)
    
    def test_calculate_segment_durations_all_empty(self, agent):
        """Test duration calculation when all segments are empty."""
        total_duration = 10.0
        segments = ["", "", ""]
        
        durations = agent._calculate_segment_durations(total_duration, segments)
        
        assert len(durations) == 3
        # Should divide equally when all empty
        assert all(d == pytest.approx(total_duration / 3) for d in durations)
    
    def test_apply_effect_ken_burns_zoom_in(self, agent):
        """Test applying ken_burns_zoom_in effect."""
        mock_clip = MagicMock()
        mock_clip.size = (1920, 1080)
        mock_clip.resized.return_value = mock_clip
        mock_clip.with_position.return_value = mock_clip
        duration = 3.0
        
        result = agent._apply_effect(mock_clip, "ken_burns_zoom_in", duration)
        
        assert result is not None
        mock_clip.resized.assert_called_once()
        mock_clip.with_position.assert_called_once()
    
    def test_apply_effect_static(self, agent):
        """Test applying static effect (no movement)."""
        mock_clip = MagicMock()
        mock_clip.size = (1920, 1080)
        duration = 3.0
        
        result = agent._apply_effect(mock_clip, "static", duration)
        
        # Static should return the original clip
        assert result == mock_clip
    
    def test_apply_effect_pan_right(self, agent):
        """Test applying pan_right effect."""
        mock_clip = MagicMock()
        mock_clip.size = (1920, 1080)
        mock_clip.resized.return_value = mock_clip
        mock_clip.with_position.return_value = mock_clip
        duration = 3.0
        
        result = agent._apply_effect(mock_clip, "pan_right", duration)
        
        assert result is not None
        mock_clip.resized.assert_called_once()
    
    def test_apply_effect_unknown_effect(self, agent):
        """Test applying unknown effect falls back to static."""
        mock_clip = MagicMock()
        mock_clip.size = (1920, 1080)
        duration = 3.0
        
        result = agent._apply_effect(mock_clip, "unknown_effect", duration)
        
        # Should fall back to static (return original clip)
        assert result == mock_clip
    
    def test_apply_effect_shake_maps_to_zoom(self, agent):
        """Test that shake effect maps to ken_burns_zoom_in."""
        mock_clip = MagicMock()
        mock_clip.size = (1920, 1080)
        mock_clip.resized.return_value = mock_clip
        mock_clip.with_position.return_value = mock_clip
        duration = 3.0
        
        result = agent._apply_effect(mock_clip, "shake", duration)
        
        # Shake should be mapped to zoom
        assert result is not None
        mock_clip.resized.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
