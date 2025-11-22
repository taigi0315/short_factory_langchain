#!/usr/bin/env python3
"""
Test Logging System | 로깅 시스템 테스트
====================================

This script demonstrates and tests the structured logging system with request ID tracking.
이 스크립트는 요청 ID 추적을 사용한 구조화된 로깅 시스템을 시연하고 테스트합니다.

Features | 기능:
- Structured logging with JSON output | JSON 출력을 사용한 구조화된 로깅
- Request ID correlation | 요청 ID 상관관계
- Contextual logging | 컨텍스트 로깅
- Performance tracking | 성능 추적

Usage | 사용법:
    python test_logging.py
    
Expected Output | 예상 출력:
    - JSON formatted log entries | JSON 형식 로그 항목
    - Request IDs in each log | 각 로그의 요청 ID
    - Structured fields | 구조화된 필드
"""

import sys
import os
import time
from datetime import datetime

# Add src to path | src를 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.logging import configure_logging
from asgi_correlation_id import correlation_id
import structlog

# Configure logging | 로깅 구성
logger = configure_logging()

def print_section(title: str, title_ko: str = ""):
    """Print a formatted section header | 형식화된 섹션 헤더 출력"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    if title_ko:
        print(f"  {title_ko}")
    print("=" * 60)

def test_basic_logging():
    """
    Test 1: Basic Structured Logging | 테스트 1: 기본 구조화 로깅
    
    Demonstrates basic logging without request ID.
    요청 ID 없이 기본 로깅을 시연합니다.
    """
    print_section("Test 1: Basic Structured Logging", "테스트 1: 기본 구조화 로깅")
    
    logger.info(
        "Application started",
        version="1.0.0",
        environment="development"
    )
    
    logger.debug(
        "Debug information",
        module="test_logging",
        function="test_basic_logging"
    )
    
    logger.warning(
        "This is a warning",
        warning_type="test",
        severity="low"
    )

def test_request_id_logging():
    """
    Test 2: Logging with Request ID | 테스트 2: 요청 ID를 사용한 로깅
    
    Demonstrates logging with correlation ID for request tracking.
    요청 추적을 위한 상관관계 ID를 사용한 로깅을 시연합니다.
    """
    print_section("Test 2: Logging with Request ID", "테스트 2: 요청 ID를 사용한 로깅")
    
    # Set request ID | 요청 ID 설정
    request_id = f"req_{int(time.time())}"
    correlation_id.set(request_id)
    
    logger.info(
        "Processing user request",
        user_id="user_123",
        action="generate_video",
        topic="Why do cats purr?"
    )
    
    logger.info(
        "Request validation passed",
        validation_time_ms=15.3,
        fields_validated=["topic", "language", "max_scenes"]
    )

def test_nested_context():
    """
    Test 3: Nested Logging Context | 테스트 3: 중첩된 로깅 컨텍스트
    
    Demonstrates logging within nested operations.
    중첩된 작업 내에서의 로깅을 시연합니다.
    """
    print_section("Test 3: Nested Logging Context", "테스트 3: 중첩된 로깅 컨텍스트")
    
    # Set new request ID | 새 요청 ID 설정
    correlation_id.set(f"req_{int(time.time())}_nested")
    
    logger.info("Starting video generation pipeline", pipeline="full")
    
    # Simulate agent operations | 에이전트 작업 시뮬레이션
    agents = [
        ("Story Finder", "story_finder", 2.5),
        ("Script Writer", "script_writer", 8.3),
        ("Image Generator", "image_gen", 25.7),
        ("Voice Synthesizer", "voice_synth", 12.1),
        ("Video Assembler", "video_assembly", 45.2)
    ]
    
    for agent_name, agent_id, duration in agents:
        logger.info(
            f"{agent_name} started",
            agent=agent_id,
            status="running"
        )
        
        time.sleep(0.1)  # Simulate work | 작업 시뮬레이션
        
        logger.info(
            f"{agent_name} completed",
            agent=agent_id,
            status="success",
            duration_seconds=duration
        )
    
    logger.info(
        "Pipeline completed successfully",
        total_duration_seconds=93.8,
        output_file="video_1732291234.mp4"
    )

def test_error_logging():
    """
    Test 4: Error Logging | 테스트 4: 오류 로깅
    
    Demonstrates error and exception logging.
    오류 및 예외 로깅을 시연합니다.
    """
    print_section("Test 4: Error Logging", "테스트 4: 오류 로깅")
    
    correlation_id.set(f"req_{int(time.time())}_error")
    
    try:
        # Simulate an error | 오류 시뮬레이션
        logger.warning(
            "API rate limit approaching",
            current_requests=95,
            limit=100,
            reset_in_seconds=45
        )
        
        # Simulate exception | 예외 시뮬레이션
        raise ValueError("Invalid scene count: must be between 3 and 10")
        
    except Exception as e:
        logger.error(
            "Video generation failed",
            error_type=type(e).__name__,
            error_message=str(e),
            recovery_action="retry_with_default_params"
        )

def test_performance_logging():
    """
    Test 5: Performance Logging | 테스트 5: 성능 로깅
    
    Demonstrates performance metrics logging.
    성능 메트릭 로깅을 시연합니다.
    """
    print_section("Test 5: Performance Logging", "테스트 5: 성능 로깅")
    
    correlation_id.set(f"req_{int(time.time())}_perf")
    
    # Simulate performance metrics | 성능 메트릭 시뮬레이션
    metrics = {
        "story_finding": {"time_ms": 3245, "tokens": 450},
        "script_writing": {"time_ms": 8123, "tokens": 1250},
        "image_generation": {"time_ms": 25678, "images": 6},
        "voice_synthesis": {"time_ms": 12345, "characters": 450},
        "video_assembly": {"time_ms": 45123, "clips": 6}
    }
    
    for operation, data in metrics.items():
        logger.info(
            f"Performance metric: {operation}",
            operation=operation,
            **data
        )
    
    total_time = sum(m["time_ms"] for m in metrics.values())
    logger.info(
        "Total pipeline performance",
        total_time_ms=total_time,
        total_time_seconds=total_time / 1000,
        operations_count=len(metrics)
    )

def test_structured_data():
    """
    Test 6: Complex Structured Data | 테스트 6: 복잡한 구조화 데이터
    
    Demonstrates logging with complex nested data structures.
    복잡한 중첩 데이터 구조를 사용한 로깅을 시연합니다.
    """
    print_section("Test 6: Complex Structured Data", "테스트 6: 복잡한 구조화 데이터")
    
    correlation_id.set(f"req_{int(time.time())}_complex")
    
    # Complex data structure | 복잡한 데이터 구조
    video_metadata = {
        "title": "Why Do Cats Purr?",
        "scenes": [
            {
                "number": 1,
                "type": "hook",
                "duration": 8.5,
                "has_animation": True
            },
            {
                "number": 2,
                "type": "explanation",
                "duration": 10.2,
                "has_animation": False
            }
        ],
        "character": {
            "type": "cat",
            "color": "orange",
            "style": "cartoon"
        },
        "generation_stats": {
            "total_time_seconds": 125.3,
            "api_calls": 15,
            "cost_usd": 0.23
        }
    }
    
    logger.info(
        "Video metadata generated",
        metadata=video_metadata,
        timestamp=datetime.now().isoformat()
    )

def main():
    """
    Main test runner | 메인 테스트 실행기
    
    Runs all logging tests in sequence.
    모든 로깅 테스트를 순차적으로 실행합니다.
    """
    print("\n" + "🔍" * 30)
    print("  ShortFactory Logging System Test")
    print("  ShortFactory 로깅 시스템 테스트")
    print("🔍" * 30)
    
    tests = [
        test_basic_logging,
        test_request_id_logging,
        test_nested_context,
        test_error_logging,
        test_performance_logging,
        test_structured_data
    ]
    
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            logger.error(
                f"Test failed: {test_func.__name__}",
                error=str(e),
                test_name=test_func.__name__
            )
    
    print_section("✓ All Logging Tests Completed", "✓ 모든 로깅 테스트 완료")
    print("\nLog Format | 로그 형식:")
    print("  - JSON structured output | JSON 구조화 출력")
    print("  - Request ID correlation | 요청 ID 상관관계")
    print("  - Timestamp in ISO 8601 | ISO 8601 형식 타임스탬프")
    print("  - Contextual fields | 컨텍스트 필드")
    print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    main()
