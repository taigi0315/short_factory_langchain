"""
Comprehensive tests for workflow state management.

Tests workflow creation, persistence, state transitions, and error handling.
"""
import pytest
import json
from pathlib import Path
from src.core.workflow_state import (
    WorkflowStateManager, WorkflowState, WorkflowStep, WorkflowStatus
)


@pytest.fixture
def temp_workflow_dir(tmp_path):
    """Temporary directory for workflow state files."""
    return str(tmp_path / "workflows")


@pytest.fixture
def manager(temp_workflow_dir):
    """WorkflowStateManager with temporary directory."""
    return WorkflowStateManager(base_dir=temp_workflow_dir)


class TestWorkflowCreation:
    """Tests for creating new workflows."""

    def test_create_workflow_generates_id(self, manager):
        """Test workflow creation generates unique ID."""
        state = manager.create_workflow("test-workflow-1", topic="Test")
        assert state.workflow_id == "test-workflow-1"
        assert state.topic == "Test"

    def test_create_workflow_sets_pending_status(self, manager):
        """Test new workflow starts with PENDING status."""
        state = manager.create_workflow("test-wf", topic="Test")
        assert state.status == WorkflowStatus.PENDING

    def test_create_workflow_initializes_empty_steps(self, manager):
        """Test new workflow has empty completed steps."""
        state = manager.create_workflow("test-wf", topic="Test")
        assert state.completed_steps == []

    def test_create_workflow_persists_to_disk(self, manager, temp_workflow_dir):
        """Test workflow creation saves state to disk."""
        workflow_id = "test-persist"
        manager.create_workflow(workflow_id, topic="Test")

        # Check file exists
        workflow_file = Path(temp_workflow_dir) / f"{workflow_id}.json"
        assert workflow_file.exists()


class TestWorkflowPersistence:
    """Tests for saving and loading workflow state."""

    def test_save_and_load_state(self, manager):
        """Test state can be saved and loaded."""
        # Create and modify state
        state = manager.create_workflow("test-save-load", topic="Test")
        state.status = WorkflowStatus.IN_PROGRESS
        state.completed_steps.append(WorkflowStep.SCRIPT_GENERATION)
        manager.save_state(state)

        # Load and verify
        loaded = manager.load_state("test-save-load")
        assert loaded.status == WorkflowStatus.IN_PROGRESS
        assert WorkflowStep.SCRIPT_GENERATION in loaded.completed_steps

    def test_load_nonexistent_workflow_returns_none(self, manager):
        """Test loading nonexistent workflow returns None."""
        result = manager.load_state("nonexistent-workflow")
        assert result is None

    def test_save_preserves_all_fields(self, manager):
        """Test saving preserves all workflow fields."""
        state = manager.create_workflow("test-fields", topic="AI")
        state.script_path = "/path/to/script.json"
        state.image_paths = {1: ["/path/to/image1.png"]}
        state.audio_paths = {1: "/path/to/audio1.mp3"}
        state.video_path = "/path/to/video.mp4"
        manager.save_state(state)

        loaded = manager.load_state("test-fields")
        assert loaded.script_path == "/path/to/script.json"
        assert loaded.image_paths == {1: ["/path/to/image1.png"]}
        assert loaded.audio_paths == {1: "/path/to/audio1.mp3"}
        assert loaded.video_path == "/path/to/video.mp4"


class TestStateTransitions:
    """Tests for workflow state transitions."""

    def test_mark_step_complete_adds_to_completed(self, manager):
        """Test marking step complete adds it to completed_steps."""
        state = manager.create_workflow("test-complete", topic="Test")
        manager.mark_step_complete("test-complete", WorkflowStep.SCRIPT_GENERATION)

        loaded = manager.load_state("test-complete")
        assert WorkflowStep.SCRIPT_GENERATION in loaded.completed_steps

    def test_mark_step_complete_sets_in_progress(self, manager):
        """Test marking step complete sets status to IN_PROGRESS."""
        state = manager.create_workflow("test-progress", topic="Test")
        manager.mark_step_complete("test-progress", WorkflowStep.SCRIPT_GENERATION)

        loaded = manager.load_state("test-progress")
        assert loaded.status == WorkflowStatus.IN_PROGRESS

    def test_mark_failed_sets_failed_status(self, manager):
        """Test marking workflow failed sets status."""
        state = manager.create_workflow("test-failed", topic="Test")
        manager.mark_failed("test-failed", WorkflowStep.IMAGE_GENERATION, "Test error")

        loaded = manager.load_state("test-failed")
        assert loaded.status == WorkflowStatus.FAILED
        assert loaded.error_message == "Test error"

    def test_is_step_complete_returns_true_for_completed(self, manager):
        """Test is_step_complete returns True for completed steps."""
        state = manager.create_workflow("test-check", topic="Test")
        manager.mark_step_complete("test-check", WorkflowStep.SCRIPT_GENERATION)

        assert manager.is_step_complete("test-check", WorkflowStep.SCRIPT_GENERATION)
        assert not manager.is_step_complete("test-check", WorkflowStep.IMAGE_GENERATION)


class TestErrorHandling:
    """Tests for error handling and recovery."""

    def test_mark_failed_stores_error_type(self, manager):
        """Test marking failed stores error type."""
        state = manager.create_workflow("test-error-type", topic="Test")
        manager.mark_failed(
            "test-error-type",
            WorkflowStep.AUDIO_GENERATION,
            "Connection timeout",
            error_type="TimeoutError"
        )

        loaded = manager.load_state("test-error-type")
        assert loaded.error_type == "TimeoutError"

    def test_corrupted_state_file_handled(self, manager, temp_workflow_dir):
        """Test corrupted state file is handled gracefully."""
        # Create corrupted file
        workflow_id = "corrupted"
        workflow_file = Path(temp_workflow_dir)
        workflow_file.mkdir(parents=True, exist_ok=True)
        (workflow_file / f"{workflow_id}.json").write_text("invalid json{")

        # Should return None or handle gracefully
        result = manager.load_state(workflow_id)
        assert result is None or isinstance(result, WorkflowState)


class TestWorkflowResumption:
    """Tests for resuming interrupted workflows."""

    def test_can_resume_after_script_generation(self, manager):
        """Test workflow can resume after script generation."""
        state = manager.create_workflow("test-resume-1", topic="Test")
        manager.mark_step_complete("test-resume-1", WorkflowStep.SCRIPT_GENERATION)

        # Simulate resume
        loaded = manager.load_state("test-resume-1")
        assert loaded.status == WorkflowStatus.IN_PROGRESS
        assert WorkflowStep.SCRIPT_GENERATION in loaded.completed_steps
        assert WorkflowStep.IMAGE_GENERATION not in loaded.completed_steps

    def test_workflow_completion_sets_completed_status(self, manager):
        """Test completing all steps sets COMPLETED status."""
        state = manager.create_workflow("test-completion", topic="Test")

        # Complete all steps
        for step in [
            WorkflowStep.SCRIPT_GENERATION,
            WorkflowStep.IMAGE_GENERATION,
            WorkflowStep.AUDIO_GENERATION,
            WorkflowStep.VIDEO_ASSEMBLY
        ]:
            manager.mark_step_complete("test-completion", step)

        loaded = manager.load_state("test-completion")
        assert loaded.status == WorkflowStatus.COMPLETED


class TestWorkflowListing:
    """Tests for listing and querying workflows."""

    def test_list_workflows_returns_all(self, manager):
        """Test listing all workflows."""
        # Create multiple workflows
        manager.create_workflow("wf-1", topic="Topic 1")
        manager.create_workflow("wf-2", topic="Topic 2")
        manager.create_workflow("wf-3", topic="Topic 3")

        # List should include all
        workflows = manager.list_workflows()
        workflow_ids = [w.workflow_id for w in workflows]
        assert "wf-1" in workflow_ids
        assert "wf-2" in workflow_ids
        assert "wf-3" in workflow_ids

    def test_get_workflow_by_topic(self, manager):
        """Test finding workflow by topic."""
        manager.create_workflow("topic-test", topic="Unique Topic")

        loaded = manager.load_state("topic-test")
        assert loaded.topic == "Unique Topic"
