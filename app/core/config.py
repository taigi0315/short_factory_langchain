"""
애플리케이션 설정 관리
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 기본 애플리케이션 설정
    app_name: str = Field(default="CognitoVid", description="애플리케이션 이름")
    app_version: str = Field(default="1.2.0", description="애플리케이션 버전")
    debug: bool = Field(default=False, description="디버그 모드")
    environment: str = Field(default="production", description="환경 (development/production)")
    
    # 서버 설정
    host: str = Field(default="0.0.0.0", description="서버 호스트")
    port: int = Field(default=8000, description="서버 포트")
    workers: int = Field(default=1, description="워커 수")
    
    # Google Cloud Platform 설정
    google_cloud_project_id: str = Field(default="demo-project", description="GCP 프로젝트 ID")
    google_application_credentials: Optional[str] = Field(None, description="GCP 서비스 계정 키 경로")
    
    # Firestore 설정
    firestore_collection_name: str = Field(default="cognitovid_jobs", description="Firestore 컬렉션 이름")
    
    # Cloud Tasks 설정
    cloud_tasks_queue_name: str = Field(default="cognitovid-queue", description="Cloud Tasks 큐 이름")
    cloud_tasks_location: str = Field(default="us-central1", description="Cloud Tasks 위치")
    
    # Redis 설정
    redis_host: str = Field(default="localhost", description="Redis 호스트")
    redis_port: int = Field(default=6379, description="Redis 포트")
    redis_db: int = Field(default=0, description="Redis 데이터베이스")
    redis_password: Optional[str] = Field(None, description="Redis 비밀번호")
    
    # AI 서비스 API 키
    google_genai_api_key: str = Field(default="demo-key", description="Google Gemini API 키")
    elevenlabs_api_key: str = Field(default="demo-key", description="ElevenLabs API 키")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API 키")
    
    # 비디오 처리 설정
    ffmpeg_path: str = Field(default="/usr/bin/ffmpeg", description="FFmpeg 경로")
    temp_dir: str = Field(default="./temp", description="임시 디렉토리")
    output_dir: str = Field(default="./outputs", description="출력 디렉토리")
    
    # 스토리지 설정
    gcs_bucket_name: str = Field(default="demo-bucket", description="GCS 버킷 이름")
    gcs_base_url: str = Field(default="https://storage.googleapis.com", description="GCS 기본 URL")
    
    # 관찰성 설정
    opentelemetry_endpoint: Optional[str] = Field(None, description="OpenTelemetry 엔드포인트")
    log_level: str = Field(default="INFO", description="로그 레벨")
    
    # 보안 설정
    secret_key: str = Field(default="demo-secret-key-for-development-only", description="시크릿 키")
    allowed_origins: List[str] = Field(default=["http://localhost:3000"], description="허용된 오리진")
    
    # 속도 제한 설정
    rate_limit_per_minute: int = Field(default=60, description="분당 요청 제한")
    rate_limit_per_hour: int = Field(default=1000, description="시간당 요청 제한")
    
    # 작업 설정
    max_video_duration: int = Field(default=180, description="최대 비디오 길이 (초)")
    max_retries: int = Field(default=3, description="최대 재시도 횟수")
    cache_ttl_hours: int = Field(default=24, description="캐시 TTL (시간)")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 전역 설정 인스턴스
settings = Settings() 