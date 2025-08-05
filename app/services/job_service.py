"""
작업 관리 서비스
"""

import uuid
from datetime import datetime
from typing import List, Optional
import structlog

from app.models.job_request import JobRequest, JobResponse
from app.models.job_status import JobStatusResponse, JobStatus
from app.models.graph_state import GraphState
from app.services.firestore_service import FirestoreService
from app.services.cloud_tasks_service import CloudTasksService
from app.core.config import settings

logger = structlog.get_logger()


class JobService:
    """작업 관리 서비스"""
    
    def __init__(self):
        self.firestore_service = FirestoreService()
        self.cloud_tasks_service = CloudTasksService()
    
    async def create_job(self, request: JobRequest) -> JobResponse:
        """새로운 비디오 생성 작업을 생성합니다."""
        
        # 작업 ID 생성
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        
        # GraphState 초기화
        initial_state = GraphState(
            job_id=job_id,
            original_query=request.query,
            target_audience=request.target_audience,
            visual_style=request.visual_style,
            target_duration=request.target_duration,
            music_style=request.music_style,
            branding_logo_url=request.branding_logo_url,
            language=request.language,
            current_step="job_created"
        )
        
        # Firestore에 작업 상태 저장
        await self.firestore_service.save_job_status(
            job_id=job_id,
            status=JobStatus.PENDING,
            state=initial_state
        )
        
        # Cloud Tasks에 작업 추가
        await self.cloud_tasks_service.create_task(
            queue_name=settings.cloud_tasks_queue_name,
            task_data={"job_id": job_id}
        )
        
        logger.info("작업 생성 완료", 
                    job_id=job_id,
                    query=request.query,
                    target_audience=request.target_audience)
        
        return JobResponse(
            job_id=job_id,
            status="pending",
            message="작업이 큐에 추가되었습니다",
            estimated_completion_time=300  # 5분 예상
        )
    
    async def get_job_status(self, job_id: str) -> JobStatusResponse:
        """작업 상태를 조회합니다."""
        
        job_data = await self.firestore_service.get_job_status(job_id)
        
        if not job_data:
            raise ValueError(f"작업을 찾을 수 없습니다: {job_id}")
        
        # 진행률 계산
        progress = self._calculate_progress(job_data.get("current_step", ""))
        
        return JobStatusResponse(
            job_id=job_id,
            status=job_data.get("status", JobStatus.PENDING),
            progress=progress,
            current_step=job_data.get("current_step"),
            created_at=job_data.get("created_at"),
            updated_at=job_data.get("updated_at"),
            completed_at=job_data.get("completed_at"),
            error_message=job_data.get("error_message"),
            video_url=job_data.get("video_url"),
            metadata=job_data.get("metadata")
        )
    
    async def cancel_job(self, job_id: str) -> bool:
        """작업을 취소합니다."""
        
        # 작업 존재 확인
        job_data = await self.firestore_service.get_job_status(job_id)
        if not job_data:
            raise ValueError(f"작업을 찾을 수 없습니다: {job_id}")
        
        # 취소 가능한 상태인지 확인
        current_status = job_data.get("status")
        if current_status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            raise ValueError(f"이미 {current_status} 상태인 작업은 취소할 수 없습니다")
        
        # 상태를 취소로 업데이트
        await self.firestore_service.update_job_status(
            job_id=job_id,
            status=JobStatus.CANCELLED,
            error_message="사용자에 의해 취소됨"
        )
        
        logger.info("작업 취소 완료", job_id=job_id)
        return True
    
    async def list_jobs(self, limit: int = 10, offset: int = 0) -> List[dict]:
        """작업 목록을 조회합니다."""
        
        jobs = await self.firestore_service.list_jobs(limit=limit, offset=offset)
        return jobs
    
    def _calculate_progress(self, current_step: str) -> float:
        """현재 단계를 기반으로 진행률을 계산합니다."""
        
        step_progress = {
            "job_created": 0.0,
            "input_moderation": 0.1,
            "prompt_writing": 0.2,
            "script_generation": 0.3,
            "truth_validation": 0.4,
            "scene_parsing": 0.5,
            "image_generation": 0.6,
            "audio_generation": 0.7,
            "video_assembly": 0.8,
            "completed": 1.0
        }
        
        return step_progress.get(current_step, 0.0) 