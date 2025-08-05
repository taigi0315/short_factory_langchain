"""
Firestore 데이터베이스 서비스
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
import structlog

from google.cloud import firestore
from app.models.job_status import JobStatus
from app.models.graph_state import GraphState
from app.core.config import settings

logger = structlog.get_logger()


class FirestoreService:
    """Firestore 데이터베이스 서비스"""
    
    def __init__(self):
        try:
            self.client = firestore.Client(project=settings.google_cloud_project_id)
            self.collection = self.client.collection(settings.firestore_collection_name)
        except Exception as e:
            logger.warning(f"Firestore 클라이언트 초기화 실패 (모킹 모드): {e}")
            self.client = None
            self.collection = None
    
    async def save_job_status(
        self, 
        job_id: str, 
        status: JobStatus, 
        state: Optional[GraphState] = None,
        **kwargs
    ) -> None:
        """작업 상태를 Firestore에 저장합니다."""
        
        if not self.client or not self.collection:
            logger.warning("Firestore 클라이언트가 초기화되지 않음 (모킹 모드)")
            return
        
        try:
            doc_data = {
                "job_id": job_id,
                "status": status.value,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                **kwargs
            }
            
            if state:
                doc_data["state"] = state.dict()
            
            doc_ref = self.collection.document(job_id)
            doc_ref.set(doc_data)
            
            logger.info("작업 상태 저장 완료", 
                        job_id=job_id, 
                        status=status.value)
                        
        except Exception as e:
            logger.error("작업 상태 저장 실패", 
                        job_id=job_id, 
                        error=str(e))
            raise
    
    async def update_job_status(
        self, 
        job_id: str, 
        status: Optional[JobStatus] = None,
        **kwargs
    ) -> None:
        """작업 상태를 업데이트합니다."""
        
        if not self.client or not self.collection:
            logger.warning("Firestore 클라이언트가 초기화되지 않음 (모킹 모드)")
            return
        
        try:
            update_data = {
                "updated_at": datetime.utcnow(),
                **kwargs
            }
            
            if status:
                update_data["status"] = status.value
            
            doc_ref = self.collection.document(job_id)
            doc_ref.update(update_data)
            
            logger.info("작업 상태 업데이트 완료", 
                        job_id=job_id, 
                        status=status.value if status else "N/A")
                        
        except Exception as e:
            logger.error("작업 상태 업데이트 실패", 
                        job_id=job_id, 
                        error=str(e))
            raise
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """작업 상태를 조회합니다."""
        
        if not self.client or not self.collection:
            logger.warning("Firestore 클라이언트가 초기화되지 않음 (모킹 모드)")
            return None
        
        try:
            doc_ref = self.collection.document(job_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                # Firestore Timestamp를 datetime으로 변환
                for key in ["created_at", "updated_at", "completed_at"]:
                    if key in data and data[key]:
                        data[key] = data[key].isoformat()
                return data
            else:
                return None
                
        except Exception as e:
            logger.error("작업 상태 조회 실패", 
                        job_id=job_id, 
                        error=str(e))
            raise
    
    async def save_graph_state(self, job_id: str, state: GraphState) -> None:
        """GraphState를 Firestore에 저장합니다."""
        
        try:
            doc_ref = self.collection.document(job_id)
            doc_ref.update({
                "state": state.dict(),
                "updated_at": datetime.utcnow(),
                "current_step": state.current_step
            })
            
            logger.info("GraphState 저장 완료", 
                        job_id=job_id, 
                        current_step=state.current_step)
                        
        except Exception as e:
            logger.error("GraphState 저장 실패", 
                        job_id=job_id, 
                        error=str(e))
            raise
    
    async def get_graph_state(self, job_id: str) -> Optional[GraphState]:
        """GraphState를 조회합니다."""
        
        try:
            doc_ref = self.collection.document(job_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                if "state" in data:
                    return GraphState(**data["state"])
            return None
            
        except Exception as e:
            logger.error("GraphState 조회 실패", 
                        job_id=job_id, 
                        error=str(e))
            raise
    
    async def list_jobs(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """작업 목록을 조회합니다."""
        
        if not self.client or not self.collection:
            logger.warning("Firestore 클라이언트가 초기화되지 않음 (모킹 모드)")
            return []
        
        try:
            query = self.collection.order_by("created_at", direction=firestore.Query.DESCENDING)
            
            if offset > 0:
                # Firestore는 offset을 직접 지원하지 않으므로 limit으로 처리
                query = query.limit(offset + limit)
            
            docs = query.stream()
            jobs = []
            
            for i, doc in enumerate(docs):
                if i >= offset:
                    data = doc.to_dict()
                    # Firestore Timestamp를 datetime으로 변환
                    for key in ["created_at", "updated_at", "completed_at"]:
                        if key in data and data[key]:
                            data[key] = data[key].isoformat()
                    jobs.append(data)
                
                if len(jobs) >= limit:
                    break
            
            return jobs
            
        except Exception as e:
            logger.error("작업 목록 조회 실패", error=str(e))
            raise
    
    async def delete_job(self, job_id: str) -> None:
        """작업을 삭제합니다."""
        
        try:
            doc_ref = self.collection.document(job_id)
            doc_ref.delete()
            
            logger.info("작업 삭제 완료", job_id=job_id)
            
        except Exception as e:
            logger.error("작업 삭제 실패", 
                        job_id=job_id, 
                        error=str(e))
            raise 