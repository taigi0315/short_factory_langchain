"""
작업 상태 정의
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """작업 상태 열거형"""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    COMPLETED_WITH_ERRORS = "completed_with_errors"


class JobStatusResponse(BaseModel):
    """작업 상태 응답 모델"""
    
    job_id: str = Field(..., description="작업 ID")
    status: JobStatus = Field(..., description="현재 작업 상태")
    progress: float = Field(default=0.0, description="진행률 (0.0 ~ 1.0)")
    current_step: Optional[str] = Field(None, description="현재 실행 중인 단계")
    created_at: datetime = Field(..., description="작업 생성 시간")
    updated_at: datetime = Field(..., description="마지막 업데이트 시간")
    completed_at: Optional[datetime] = Field(None, description="완료 시간")
    error_message: Optional[str] = Field(None, description="오류 메시지")
    video_url: Optional[str] = Field(None, description="생성된 비디오 URL")
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 메타데이터")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_1234567890",
                "status": "processing",
                "progress": 0.6,
                "current_step": "image_generation",
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:05:00Z",
                "completed_at": None,
                "error_message": None,
                "video_url": None,
                "metadata": {
                    "estimated_completion_time": 300,
                    "total_steps": 8,
                    "completed_steps": 5
                }
            }
        } 