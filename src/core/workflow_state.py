"""
Workflow State Management
Tracks progress of video generation workflows and enables resume functionality.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal
from datetime import datetime
from pathlib import Path
import json
import structlog
from enum import Enum

logger = structlog.get_logger()


class WorkflowStep(str, Enum):
    """Workflow steps in order of execution."""
    SCRIPT_GENERATION = "script_generation"
    IMAGE_GENERATION = "image_generation"
    AUDIO_GENERATION = "audio_generation"
    VIDEO_ASSEMBLY = "video_assembly"


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    FAILED = "failed"
    COMPLETED = "completed"


class WorkflowState(BaseModel):
    """
    Represents the state of a video generation workflow.
    Saved as JSON to enable resume functionality.
    """
    
    # Identification
    workflow_id: str = Field(description="Unique workflow identifier")
    
    # Status
    status: WorkflowStatus = Field(default=WorkflowStatus.PENDING)
    current_step: Optional[WorkflowStep] = Field(default=None)
    completed_steps: List[WorkflowStep] = Field(default_factory=list)
    failed_step: Optional[WorkflowStep] = Field(default=None)
    
    # Error information
    error_message: Optional[str] = Field(default=None)
    error_type: Optional[str] = Field(default=None)
    
    # Input parameters
    topic: Optional[str] = Field(default=None)
    duration: Optional[str] = Field(default=None)
    
    # Generated artifacts (paths relative to workflow directory)
    script_path: Optional[str] = Field(default=None)
    image_paths: Dict[int, str] = Field(default_factory=dict)  # scene_number -> path
    audio_paths: Dict[int, str] = Field(default_factory=dict)  # scene_number -> path
    video_path: Optional[str] = Field(default=None)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    
    # Progress tracking
    total_scenes: Optional[int] = Field(default=None)
    images_completed: int = Field(default=0)
    audio_completed: int = Field(default=0)
    
    class Config:
        use_enum_values = True


class WorkflowStateManager:
    """Manages workflow state persistence."""
    
    def __init__(self, base_dir: str = "generated_assets/workflows"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_workflow_dir(self, workflow_id: str) -> Path:
        """Get directory for a specific workflow."""
        return self.base_dir / workflow_id
    
    def _get_state_path(self, workflow_id: str) -> Path:
        """Get path to state file for a workflow."""
        return self._get_workflow_dir(workflow_id) / "state.json"
    
    def create_workflow(
        self,
        workflow_id: str,
        topic: Optional[str] = None,
        duration: Optional[str] = None
    ) -> WorkflowState:
        """
        Create a new workflow and save initial state.
        
        Args:
            workflow_id: Unique identifier for the workflow
            topic: Video topic
            duration: Video duration
            
        Returns:
            WorkflowState: Initial workflow state
        """
        # Create workflow directory
        workflow_dir = self._get_workflow_dir(workflow_id)
        workflow_dir.mkdir(parents=True, exist_ok=True)
        
        # Create initial state
        state = WorkflowState(
            workflow_id=workflow_id,
            topic=topic,
            duration=duration,
            status=WorkflowStatus.PENDING
        )
        
        # Save state
        self.save_state(state)
        
        logger.info("Workflow created", workflow_id=workflow_id, topic=topic)
        return state
    
    def save_state(self, state: WorkflowState) -> None:
        """
        Save workflow state to disk.
        
        Args:
            state: Workflow state to save
        """
        state.updated_at = datetime.utcnow()
        
        state_path = self._get_state_path(state.workflow_id)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(state_path, 'w') as f:
            json.dump(state.model_dump(mode='json'), f, indent=2, default=str)
        
        logger.debug("Workflow state saved", 
                    workflow_id=state.workflow_id,
                    status=state.status,
                    current_step=state.current_step)
    
    def load_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """
        Load workflow state from disk.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            WorkflowState if found, None otherwise
        """
        state_path = self._get_state_path(workflow_id)
        
        if not state_path.exists():
            logger.warning("Workflow state not found", workflow_id=workflow_id)
            return None
        
        try:
            with open(state_path, 'r') as f:
                data = json.load(f)
            
            state = WorkflowState(**data)
            logger.debug("Workflow state loaded", workflow_id=workflow_id)
            return state
            
        except Exception as e:
            logger.error("Failed to load workflow state", 
                        workflow_id=workflow_id,
                        error=str(e))
            return None
    
    def update_step(
        self,
        workflow_id: str,
        step: WorkflowStep,
        status: WorkflowStatus = WorkflowStatus.IN_PROGRESS
    ) -> WorkflowState:
        """
        Update current workflow step.
        
        Args:
            workflow_id: Workflow identifier
            step: Current step
            status: Workflow status
            
        Returns:
            Updated workflow state
        """
        state = self.load_state(workflow_id)
        if not state:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        state.current_step = step
        state.status = status
        
        self.save_state(state)
        logger.info("Workflow step updated", 
                   workflow_id=workflow_id,
                   step=step,
                   status=status)
        return state
    
    def mark_step_complete(
        self,
        workflow_id: str,
        step: WorkflowStep
    ) -> WorkflowState:
        """
        Mark a workflow step as completed.
        
        Args:
            workflow_id: Workflow identifier
            step: Completed step
            
        Returns:
            Updated workflow state
        """
        state = self.load_state(workflow_id)
        if not state:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        if step not in state.completed_steps:
            state.completed_steps.append(step)
        
        self.save_state(state)
        logger.info("Workflow step completed", 
                   workflow_id=workflow_id,
                   step=step,
                   completed_steps=len(state.completed_steps))
        return state
    
    def mark_failed(
        self,
        workflow_id: str,
        step: WorkflowStep,
        error_message: str,
        error_type: Optional[str] = None
    ) -> WorkflowState:
        """
        Mark workflow as failed.
        
        Args:
            workflow_id: Workflow identifier
            step: Step that failed
            error_message: Error description
            error_type: Type of error
            
        Returns:
            Updated workflow state
        """
        state = self.load_state(workflow_id)
        if not state:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        state.status = WorkflowStatus.FAILED
        state.failed_step = step
        state.error_message = error_message
        state.error_type = error_type
        
        self.save_state(state)
        logger.error("Workflow failed", 
                    workflow_id=workflow_id,
                    step=step,
                    error=error_message)
        return state
    
    def mark_completed(self, workflow_id: str) -> WorkflowState:
        """
        Mark workflow as completed.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Updated workflow state
        """
        state = self.load_state(workflow_id)
        if not state:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        state.status = WorkflowStatus.COMPLETED
        state.completed_at = datetime.utcnow()
        
        self.save_state(state)
        logger.info("Workflow completed", workflow_id=workflow_id)
        return state
    
    def save_script(
        self,
        workflow_id: str,
        script_path: str,
        total_scenes: int
    ) -> WorkflowState:
        """
        Save script generation result.
        
        Args:
            workflow_id: Workflow identifier
            script_path: Path to saved script
            total_scenes: Number of scenes in script
            
        Returns:
            Updated workflow state
        """
        state = self.load_state(workflow_id)
        if not state:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        state.script_path = script_path
        state.total_scenes = total_scenes
        
        self.save_state(state)
        logger.info("Script saved to workflow", 
                   workflow_id=workflow_id,
                   total_scenes=total_scenes)
        return state
    
    def save_image(
        self,
        workflow_id: str,
        scene_number: int,
        image_path: str
    ) -> WorkflowState:
        """
        Save image generation result (incremental).
        
        Args:
            workflow_id: Workflow identifier
            scene_number: Scene number
            image_path: Path to saved image
            
        Returns:
            Updated workflow state
        """
        state = self.load_state(workflow_id)
        if not state:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        state.image_paths[scene_number] = image_path
        state.images_completed = len(state.image_paths)
        
        self.save_state(state)
        logger.info("Image saved to workflow", 
                   workflow_id=workflow_id,
                   scene_number=scene_number,
                   progress=f"{state.images_completed}/{state.total_scenes}")
        return state
    
    def save_audio(
        self,
        workflow_id: str,
        scene_number: int,
        audio_path: str
    ) -> WorkflowState:
        """
        Save audio generation result (incremental).
        
        Args:
            workflow_id: Workflow identifier
            scene_number: Scene number
            audio_path: Path to saved audio
            
        Returns:
            Updated workflow state
        """
        state = self.load_state(workflow_id)
        if not state:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        state.audio_paths[scene_number] = audio_path
        state.audio_completed = len(state.audio_paths)
        
        self.save_state(state)
        logger.info("Audio saved to workflow", 
                   workflow_id=workflow_id,
                   scene_number=scene_number,
                   progress=f"{state.audio_completed}/{state.total_scenes}")
        return state
    
    def save_video(
        self,
        workflow_id: str,
        video_path: str
    ) -> WorkflowState:
        """
        Save video assembly result.
        
        Args:
            workflow_id: Workflow identifier
            video_path: Path to saved video
            
        Returns:
            Updated workflow state
        """
        state = self.load_state(workflow_id)
        if not state:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        state.video_path = video_path
        
        self.save_state(state)
        logger.info("Video saved to workflow", 
                   workflow_id=workflow_id,
                   video_path=video_path)
        return state
    
    def list_workflows(
        self,
        status: Optional[WorkflowStatus] = None
    ) -> List[WorkflowState]:
        """
        List all workflows, optionally filtered by status.
        
        Args:
            status: Optional status filter
            
        Returns:
            List of workflow states
        """
        workflows = []
        
        for workflow_dir in self.base_dir.iterdir():
            if workflow_dir.is_dir():
                state = self.load_state(workflow_dir.name)
                if state and (status is None or state.status == status):
                    workflows.append(state)
        
        # Sort by creation time (newest first)
        workflows.sort(key=lambda w: w.created_at, reverse=True)
        
        return workflows


# Global instance
workflow_manager = WorkflowStateManager()
