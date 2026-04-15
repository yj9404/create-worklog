import sys
from unittest.mock import MagicMock
# Mock requests
mock_requests = MagicMock()
class MockHTTPError(Exception):
    pass
mock_requests.exceptions.HTTPError = MockHTTPError
sys.modules["requests"] = mock_requests

import unittest
from test_create_worklog import TestCreateWorklog

if __name__ == '__main__':
    unittest.main()
