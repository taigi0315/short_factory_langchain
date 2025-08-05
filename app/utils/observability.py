"""
관찰성 설정 - OpenTelemetry, 모니터링
"""

import os
from app.core.config import settings


def setup_observability():
    """관찰성 시스템 설정"""
    
    if not settings.opentelemetry_endpoint:
        return
    
    try:
        # OpenTelemetry가 설치되어 있는지 확인
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        except ImportError:
            import structlog
            logger = structlog.get_logger()
            logger.warning("OpenTelemetry가 설치되지 않았습니다. 관찰성 기능이 비활성화됩니다.")
            return
        
        # Tracer Provider 설정
        provider = TracerProvider()
        trace.set_tracer_provider(provider)
        
        # OTLP Exporter 설정
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.opentelemetry_endpoint,
            insecure=True  # 개발 환경용
        )
        
        # Batch Span Processor 설정
        processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(processor)
        
        # FastAPI 자동 계측
        FastAPIInstrumentor.instrument()
        
        # HTTPX 클라이언트 자동 계측
        HTTPXClientInstrumentor.instrument()
        
        # 환경 변수 설정
        os.environ["OTEL_SERVICE_NAME"] = settings.app_name
        os.environ["OTEL_SERVICE_VERSION"] = settings.app_version
        
        import structlog
        logger = structlog.get_logger()
        logger.info("관찰성 시스템 설정 완료")
        
    except Exception as e:
        # 관찰성 설정 실패 시 로그만 남기고 계속 진행
        import structlog
        logger = structlog.get_logger()
        logger.warning("관찰성 시스템 설정 실패", error=str(e)) 