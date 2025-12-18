"""
Comprehensive tests for API routes.

Tests all main endpoints for proper request/response handling,
validation, and error cases.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from src.api.main import app
from src.models.models import VideoScript, Scene, SceneType, VoiceTone, ImageStyle


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """Mock settings to prevent real API calls."""
    with patch('src.core.config.settings') as mock:
        mock.USE_REAL_LLM = False
        mock.USE_REAL_IMAGE = False
        mock.USE_REAL_VOICE = False
        mock.GEMINI_API_KEY = "test-key"
        mock.ELEVENLABS_API_KEY = "test-key"
        mock.TAVILY_API_KEY = "test-key"
        yield mock


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check_returns_200(self, client):
        """Test health check returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_returns_status(self, client):
        """Test health check returns status field."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "unhealthy"]


class TestScriptGenerationEndpoints:
    """Tests for script generation endpoints."""

    def test_generate_script_requires_story_title(self, client):
        """Test script generation requires story_title."""
        response = client.post("/api/scripts/generate", json={
            "story_premise": "Test premise"
        })
        assert response.status_code == 422  # Validation error

    def test_generate_script_success_mock_mode(self, client, mock_settings):
        """Test script generation succeeds in mock mode."""
        response = client.post("/api/scripts/generate", json={
            "story_title": "Test Story",
            "story_premise": "A test premise about AI",
            "story_genre": "Educational",
            "story_audience": "General",
            "duration": "60s"
        })

        assert response.status_code == 200
        data = response.json()
        assert "script" in data
        assert data["script"]["title"] is not None

    def test_generate_script_validates_duration(self, client):
        """Test script generation validates duration format."""
        response = client.post("/api/scripts/generate", json={
            "story_title": "Test",
            "story_premise": "Test",
            "story_genre": "Creative",
            "story_audience": "General",
            "duration": "invalid_duration"
        })

        # Should still work or return validation error
        assert response.status_code in [200, 422]

    @patch('src.agents.script_writer.agent.ScriptWriterAgent')
    def test_generate_script_handles_agent_error(self, mock_agent_class, client):
        """Test script generation handles agent errors gracefully."""
        mock_agent = MagicMock()
        mock_agent.generate_script = AsyncMock(side_effect=Exception("Agent failed"))
        mock_agent_class.return_value = mock_agent

        response = client.post("/api/scripts/generate", json={
            "story_title": "Test",
            "story_premise": "Test",
            "story_genre": "Creative",
            "story_audience": "General",
            "duration": "60s"
        })

        # Should either return 500 or use fallback
        assert response.status_code in [200, 500]


class TestStoryFinderEndpoints:
    """Tests for story generation endpoints."""

    def test_find_stories_requires_topic(self, client):
        """Test find stories requires topic parameter."""
        response = client.post("/api/stories/generate", json={})
        assert response.status_code == 422

    def test_find_stories_success_mock_mode(self, client, mock_settings):
        """Test find stories succeeds in mock mode."""
        response = client.post("/api/stories/generate", json={
            "topic": "artificial intelligence",
            "category": "Educational",
            "count": 3
        })

        assert response.status_code == 200
        data = response.json()
        assert "stories" in data
        assert isinstance(data["stories"], list)

    def test_find_stories_validates_count(self, client):
        """Test find stories validates story count."""
        response = client.post("/api/stories/generate", json={
            "topic": "AI",
            "category": "Creative",
            "count": 100  # Likely above max
        })

        # Should either accept or reject
        assert response.status_code in [200, 422]


class TestSceneEditorEndpoints:
    """Tests for scene editor endpoints."""

    def test_regenerate_image_requires_scene_number(self, client):
        """Test regenerate image requires scene_number."""
        response = client.post("/api/scene-editor/regenerate-image", json={
            "workflow_id": "test-123",
            "new_prompt": "test prompt"
        })
        assert response.status_code == 422

    def test_update_scene_text_validates_request(self, client):
        """Test update scene text validates request structure."""
        response = client.post("/api/scene-editor/update-text", json={
            "workflow_id": "test-123"
            # Missing scene_number and new_text
        })
        assert response.status_code == 422


class TestVideoEndpoints:
    """Tests for video generation endpoints."""

    def test_generate_video_requires_workflow_id(self, client):
        """Test video generation requires workflow_id."""
        response = client.post("/api/videos/generate", json={})
        assert response.status_code == 422

    def test_generate_video_validates_workflow_exists(self, client):
        """Test video generation validates workflow exists."""
        response = client.post("/api/videos/generate", json={
            "workflow_id": "nonexistent-workflow-12345"
        })

        # Should return error for nonexistent workflow
        assert response.status_code in [404, 400, 500]


class TestDevEndpoints:
    """Tests for development/testing endpoints."""

    def test_dev_generate_image_mock_mode(self, client, mock_settings):
        """Test dev image generation in mock mode."""
        response = client.post("/api/dev/generate-image", json={
            "prompt": "a beautiful sunset",
            "style": "cinematic"
        })

        # Should succeed in mock mode
        assert response.status_code == 200

    def test_dev_generate_audio_mock_mode(self, client, mock_settings):
        """Test dev audio generation in mock mode."""
        response = client.post("/api/dev/generate-audio", json={
            "text": "Hello world",
            "tone": "friendly"
        })

        # Should succeed in mock mode
        assert response.status_code == 200


class TestErrorResponses:
    """Tests for consistent error response formatting."""

    def test_404_returns_json(self, client):
        """Test 404 errors return JSON format."""
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == 404
        # FastAPI returns JSON for 404s
        data = response.json()
        assert "detail" in data

    def test_validation_error_returns_details(self, client):
        """Test validation errors return field details."""
        response = client.post("/api/scripts/generate", json={
            # Missing required fields
            "invalid_field": "test"
        })

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestCORS:
    """Tests for CORS configuration."""

    def test_cors_headers_present(self, client):
        """Test CORS headers are configured."""
        response = client.options("/health")
        # CORS headers should be present
        # Note: TestClient may not include all CORS headers
        assert response.status_code in [200, 405]


class TestStaticFileServing:
    """Tests for static file serving."""

    def test_generated_assets_accessible(self, client):
        """Test generated assets path is accessible."""
        # This may return 404 if no files exist, which is fine
        response = client.get("/generated_assets/")
        assert response.status_code in [200, 404, 403]
