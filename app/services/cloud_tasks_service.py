"""
Google Cloud Tasks 서비스
"""

import json
from typing import Dict, Any
import structlog

from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2
from app.core.config import settings
from datetime import datetime, timedelta

logger = structlog.get_logger()


class CloudTasksService:
    """Google Cloud Tasks 서비스"""
    
    def __init__(self):
        try:
            self.client = tasks_v2.CloudTasksClient()
            self.project_id = settings.google_cloud_project_id
            self.location = settings.cloud_tasks_location
        except Exception as e:
            logger.warning(f"Cloud Tasks 클라이언트 초기화 실패 (모킹 모드): {e}")
            self.client = None
            self.project_id = settings.google_cloud_project_id
            self.location = settings.cloud_tasks_location
    
    async def create_task(self, queue_name: str, task_data: Dict[str, Any]) -> str:
        """Cloud Tasks에 새 작업을 생성합니다."""
        
        if not self.client:
            logger.warning("Cloud Tasks 클라이언트가 초기화되지 않음 (모킹 모드)")
            return f"mock_task_{queue_name}_{hash(str(task_data))}"
        
        try:
            # 큐 경로 구성
            queue_path = self.client.queue_path(self.project_id, self.location, queue_name)
            
            # 작업 데이터를 JSON으로 직렬화
            task_data_json = json.dumps(task_data)
            
            # HTTP 요청 구성
            http_request = tasks_v2.HttpRequest(
                http_method=tasks_v2.HttpMethod.POST,
                url=f"https://{self.project_id}.run.app/process-job",  # Cloud Run 워커 엔드포인트
                headers={"Content-Type": "application/json"},
                body=task_data_json.encode()
            )
            
            # 작업 생성
            task = tasks_v2.Task(http_request=http_request)
            response = self.client.create_task(request={"parent": queue_path, "task": task})
            
            logger.info("Cloud Tasks 작업 생성 완료", 
                        queue_name=queue_name,
                        task_name=response.name)
            
            return response.name
            
        except Exception as e:
            logger.error("Cloud Tasks 작업 생성 실패", 
                        queue_name=queue_name,
                        error=str(e))
            raise
    
    async def create_task_with_delay(
        self, 
        queue_name: str, 
        task_data: Dict[str, Any], 
        delay_seconds: int
    ) -> str:
        """지연 시간을 가진 Cloud Tasks 작업을 생성합니다."""
        
        try:
            # 큐 경로 구성
            queue_path = self.client.queue_path(self.project_id, self.location, queue_name)
            
            # 작업 데이터를 JSON으로 직렬화
            task_data_json = json.dumps(task_data)
            
            # 지연 시간 설정
            timestamp = timestamp_pb2.Timestamp()
            timestamp.FromDatetime(
                datetime.utcnow() + timedelta(seconds=delay_seconds)
            )
            
            # HTTP 요청 구성
            http_request = tasks_v2.HttpRequest(
                http_method=tasks_v2.HttpMethod.POST,
                url=f"https://{self.project_id}.run.app/process-job",
                headers={"Content-Type": "application/json"},
                body=task_data_json.encode()
            )
            
            # 작업 생성 (지연 시간 포함)
            task = tasks_v2.Task(
                http_request=http_request,
                schedule_time=timestamp
            )
            response = self.client.create_task(request={"parent": queue_path, "task": task})
            
            logger.info("지연 Cloud Tasks 작업 생성 완료", 
                        queue_name=queue_name,
                        task_name=response.name,
                        delay_seconds=delay_seconds)
            
            return response.name
            
        except Exception as e:
            logger.error("지연 Cloud Tasks 작업 생성 실패", 
                        queue_name=queue_name,
                        error=str(e))
            raise
    
    async def delete_task(self, task_name: str) -> None:
        """Cloud Tasks 작업을 삭제합니다."""
        
        try:
            self.client.delete_task(request={"name": task_name})
            
            logger.info("Cloud Tasks 작업 삭제 완료", task_name=task_name)
            
        except Exception as e:
            logger.error("Cloud Tasks 작업 삭제 실패", 
                        task_name=task_name,
                        error=str(e))
            raise
    
    async def get_queue_info(self, queue_name: str) -> Dict[str, Any]:
        """큐 정보를 조회합니다."""
        
        try:
            queue_path = self.client.queue_path(self.project_id, self.location, queue_name)
            queue = self.client.get_queue(request={"name": queue_path})
            
            return {
                "name": queue.name,
                "state": queue.state.name,
                "rate_limits": {
                    "max_dispatches_per_second": queue.rate_limits.max_dispatches_per_second,
                    "max_concurrent_dispatches": queue.rate_limits.max_concurrent_dispatches
                },
                "retry_config": {
                    "max_attempts": queue.retry_config.max_attempts,
                    "max_retry_duration": queue.retry_config.max_retry_duration.total_seconds()
                }
            }
            
        except Exception as e:
            logger.error("큐 정보 조회 실패", 
                        queue_name=queue_name,
                        error=str(e))
            raise 