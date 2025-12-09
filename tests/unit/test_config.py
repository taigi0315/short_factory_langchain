
import unittest
from src.core.config import settings

class TestConfig(unittest.TestCase):
    def test_default_request_timeout(self):
        """Test that the default request timeout is set to 300.0 seconds (5 minutes)."""
        # We access the value from the instantiated settings object
        self.assertEqual(settings.DEFAULT_REQUEST_TIMEOUT, 300.0, "Default request timeout should be 300.0 seconds")

    def test_timeout_constraints(self):
        """Test that the timeout value respects min/max constraints if possible.
        Since we are testing the Pydantic model defaults, we can checks field info.
        """
        # We can inspect the field definition if needed, but testing the value is the primary goal.
        # Let's double check it's not the old 30.0
        self.assertNotEqual(settings.DEFAULT_REQUEST_TIMEOUT, 30.0)
