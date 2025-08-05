"""
LangGraph 상태 모델
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class Scene(BaseModel):
    """비디오 장면 모델"""
    
    scene_id: str = Field(..., description="장면 ID")
    start_time: float = Field(..., description="시작 시간 (초)")
    end_time: float = Field(..., description="종료 시간 (초)")
    duration: float = Field(..., description="장면 길이 (초)")
    script_segment: str = Field(..., description="해당 장면의 스크립트")
    image_prompt: str = Field(..., description="이미지 생성 프롬프트")
    image_url: Optional[str] = Field(None, description="생성된 이미지 URL")
    image_path: Optional[str] = Field(None, description="로컬 이미지 경로")


class GraphState(BaseModel):
    """LangGraph 상태 모델"""
    
    # 작업 기본 정보
    job_id: str = Field(..., description="작업 ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="생성 시간")
    
    # 사용자 입력
    original_query: str = Field(..., description="원본 사용자 쿼리")
    target_audience: str = Field(..., description="대상 연령층")
    visual_style: str = Field(..., description="시각 스타일")
    target_duration: int = Field(..., description="목표 비디오 길이")
    music_style: Optional[str] = Field(None, description="음악 스타일")
    branding_logo_url: Optional[str] = Field(None, description="브랜딩 로고 URL")
    language: str = Field(..., description="언어")
    
    # 처리 단계별 결과
    moderation_result: Optional[Dict[str, Any]] = Field(None, description="모더레이션 결과")
    meta_prompt: Optional[str] = Field(None, description="메타 프롬프트")
    raw_script: Optional[str] = Field(None, description="원본 스크립트")
    validation_result: Optional[Dict[str, Any]] = Field(None, description="검증 결과")
    validated_script: Optional[str] = Field(None, description="검증된 스크립트")
    scenes: List[Scene] = Field(default_factory=list, description="장면 목록")
    audio_url: Optional[str] = Field(None, description="오디오 파일 URL")
    audio_path: Optional[str] = Field(None, description="로컬 오디오 경로")
    word_timestamps: Optional[List[Dict[str, Any]]] = Field(None, description="단어별 타임스탬프")
    final_video_url: Optional[str] = Field(None, description="최종 비디오 URL")
    final_video_path: Optional[str] = Field(None, description="로컬 비디오 경로")
    
    # 오류 및 상태 정보
    current_step: Optional[str] = Field(None, description="현재 실행 중인 단계")
    error_message: Optional[str] = Field(None, description="오류 메시지")
    retry_count: int = Field(default=0, description="재시도 횟수")
    warnings: List[str] = Field(default_factory=list, description="경고 메시지 목록")
    
    # 메타데이터
    processing_time: Optional[float] = Field(None, description="총 처리 시간 (초)")
    api_costs: Optional[Dict[str, float]] = Field(None, description="API 비용 추정")
    
    class Config:
        arbitrary_types_allowed = True 