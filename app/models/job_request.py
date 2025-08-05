"""
작업 요청 및 응답 모델
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field, validator


class JobRequest(BaseModel):
    """비디오 생성 작업 요청 모델"""
    
    # 필수 필드
    query: str = Field(..., description="설명할 개념이나 용어", min_length=1, max_length=500)
    target_audience: Literal["child", "teenager", "university_student", "expert"] = Field(
        default="university_student", 
        description="대상 연령층"
    )
    
    # 선택적 필드
    visual_style: Literal["photorealistic", "cartoon", "whiteboard_style_image", "infographic"] = Field(
        default="whiteboard_style_image",
        description="시각 스타일"
    )
    target_duration: int = Field(
        default=60,
        description="목표 비디오 길이 (초)",
        ge=30,
        le=180
    )
    music_style: Optional[Literal["inspirational", "calm", "upbeat", "none"]] = Field(
        default="calm",
        description="배경 음악 스타일"
    )
    branding_logo_url: Optional[str] = Field(
        None,
        description="브랜딩 로고 URL"
    )
    language: str = Field(
        default="ko-KR",
        description="언어 코드 (예: ko-KR, en-US, es-ES)"
    )
    
    @validator('query')
    def validate_query(cls, v):
        """쿼리 검증"""
        if not v.strip():
            raise ValueError("쿼리는 비어있을 수 없습니다")
        return v.strip()
    
    @validator('target_duration')
    def validate_duration(cls, v):
        """비디오 길이 검증"""
        if v < 30:
            raise ValueError("비디오 길이는 최소 30초여야 합니다")
        if v > 180:
            raise ValueError("비디오 길이는 최대 180초여야 합니다")
        return v
    
    @validator('branding_logo_url')
    def validate_logo_url(cls, v):
        """로고 URL 검증"""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError("로고 URL은 유효한 HTTP/HTTPS URL이어야 합니다")
        return v


class JobResponse(BaseModel):
    """작업 생성 응답 모델"""
    
    job_id: str = Field(..., description="작업 ID")
    status: str = Field(default="pending", description="작업 상태")
    message: str = Field(default="작업이 큐에 추가되었습니다", description="응답 메시지")
    estimated_completion_time: Optional[int] = Field(
        None, 
        description="예상 완료 시간 (초)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_1234567890",
                "status": "pending",
                "message": "작업이 큐에 추가되었습니다",
                "estimated_completion_time": 300
            }
        } 