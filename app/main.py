"""
CognitoVid FastAPI 애플리케이션 메인 진입점
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.core.config import settings
from app.api.routes import router as api_router
from app.utils.logging import setup_logging
from app.utils.observability import setup_observability


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    try:
        # 시작 시 실행
        setup_logging()
        setup_observability()
        
        # 필요한 디렉토리 생성
        os.makedirs(settings.temp_dir, exist_ok=True)
        os.makedirs(settings.output_dir, exist_ok=True)
        
        logger = structlog.get_logger()
        logger.info("CognitoVid 애플리케이션 시작", 
                    version=settings.app_version,
                    environment=settings.environment)
        
        yield
        
        # 종료 시 실행
        logger.info("CognitoVid 애플리케이션 종료")
    except Exception as e:
        print(f"Lifespan 오류: {e}")
        yield


# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI 기반 교육용 비디오 자동 생성 시스템",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "CognitoVid API에 오신 것을 환영합니다!",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "문서는 개발 모드에서만 사용 가능합니다"
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """전역 예외 처리"""
    logger = structlog.get_logger()
    logger.error("예상치 못한 오류 발생", 
                error=str(exc),
                path=request.url.path,
                method=request.method)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "내부 서버 오류가 발생했습니다",
            "message": "문제가 지속되면 관리자에게 문의하세요"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.workers
    ) 