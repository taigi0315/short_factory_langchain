#!/usr/bin/env python3
"""Test script to verify structured logging with request ID."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.logging import configure_logging
from asgi_correlation_id import correlation_id
import structlog

# Configure logging
logger = configure_logging()

# Test 1: Basic logging
print("=" * 50)
print("Test 1: Basic structured logging")
print("=" * 50)
logger.info("Test message without request ID", test_field="value1")

# Test 2: With request ID
print("\n" + "=" * 50)
print("Test 2: Logging with request ID")
print("=" * 50)
correlation_id.set("test-request-123")
logger.info("Test message with request ID", test_field="value2", user="test_user")

# Test 3: Nested context
print("\n" + "=" * 50)
print("Test 3: Nested logging context")
print("=" * 50)
correlation_id.set("test-request-456")
logger.info("Starting operation", operation="test_operation")
logger.warning("Warning during operation", issue="test_issue")
logger.info("Operation completed", status="success")

print("\n" + "=" * 50)
print("✓ All logging tests completed")
print("=" * 50)
