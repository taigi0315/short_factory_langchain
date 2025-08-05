"""
API 라우터 정의
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import structlog

from app.models.job_request import JobRequest, JobResponse
from app.models.job_status import JobStatusResponse, JobStatus
from app.services.job_service import JobService
from app.core.config import settings

router = APIRouter()
logger = structlog.get_logger()


@router.post("/generate", response_model=JobResponse)
async def create_video_generation_job(
    request: JobRequest,
    background_tasks: BackgroundTasks
):
    """
    비디오 생성 작업을 생성하고 큐에 추가합니다.
    
    Args:
        request: 비디오 생성 요청 데이터
        background_tasks: 백그라운드 작업 관리자
    
    Returns:
        JobResponse: 생성된 작업 정보
    """
    try:
        logger.info("비디오 생성 작업 요청", 
                    query=request.query,
                    target_audience=request.target_audience,
                    visual_style=request.visual_style)
        
        job_service = JobService()
        job_response = await job_service.create_job(request)
        
        logger.info("작업 생성 완료", job_id=job_response.job_id)
        return job_response
        
    except Exception as e:
        logger.error("작업 생성 실패", error=str(e))
        raise HTTPException(status_code=500, detail="작업 생성 중 오류가 발생했습니다")


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    작업 상태를 조회합니다.
    
    Args:
        job_id: 작업 ID
    
    Returns:
        JobStatusResponse: 작업 상태 정보
    """
    try:
        logger.info("작업 상태 조회", job_id=job_id)
        
        job_service = JobService()
        status_response = await job_service.get_job_status(job_id)
        
        return status_response
        
    except ValueError as e:
        logger.warning("작업을 찾을 수 없음", job_id=job_id, error=str(e))
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")
    except Exception as e:
        logger.error("작업 상태 조회 실패", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail="작업 상태 조회 중 오류가 발생했습니다")


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """
    작업을 취소합니다.
    
    Args:
        job_id: 작업 ID
    
    Returns:
        취소 결과
    """
    try:
        logger.info("작업 취소 요청", job_id=job_id)
        
        job_service = JobService()
        result = await job_service.cancel_job(job_id)
        
        return {"message": "작업이 성공적으로 취소되었습니다", "job_id": job_id}
        
    except ValueError as e:
        logger.warning("취소할 작업을 찾을 수 없음", job_id=job_id, error=str(e))
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")
    except Exception as e:
        logger.error("작업 취소 실패", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail="작업 취소 중 오류가 발생했습니다")


@router.get("/jobs")
async def list_jobs(limit: int = 10, offset: int = 0):
    """
    작업 목록을 조회합니다.
    
    Args:
        limit: 조회할 작업 수 (기본값: 10)
        offset: 건너뛸 작업 수 (기본값: 0)
    
    Returns:
        작업 목록
    """
    try:
        logger.info("작업 목록 조회", limit=limit, offset=offset)
        
        job_service = JobService()
        jobs = await job_service.list_jobs(limit=limit, offset=offset)
        
        return {
            "jobs": jobs,
            "total": len(jobs),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error("작업 목록 조회 실패", error=str(e))
        raise HTTPException(status_code=500, detail="작업 목록 조회 중 오류가 발생했습니다") 