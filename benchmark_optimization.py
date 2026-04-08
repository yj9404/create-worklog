import time
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Mock requests before importing create_worklog
sys.modules['requests'] = MagicMock()

# Mock environment variables
os.environ["BASE_URL"] = "https://test.atlassian.net/wiki/rest/api"
os.environ["BASE_URL_V1"] = "https://test.atlassian.net/wiki/rest/api/v1"
os.environ["SPACE_ID"] = "12345"
os.environ["TEMPLATE_ID"] = "67890"
os.environ["ROOT_FOLDER_ID"] = "111213"
os.environ["ATLASSIAN_USER"] = "test@example.com"
os.environ["ATLASSIAN_API_TOKEN"] = "test_token"

import create_worklog
import requests

def benchmark():
    # Setup large number of children
    num_children = 10000
    children = [{"title": f"folder_{i}", "id": str(i)} for i in range(num_children)]

    mock_response = Mock()
    mock_response.json.return_value = {
        "directChildren": {
            "results": children
        }
    }
    mock_response.raise_for_status.return_value = None

    requests.get.return_value = mock_response

    # Warm up and measurement
    start_time = time.perf_counter()
    # Search for a folder that is near the end or not there to ensure we iterate
    create_worklog.get_folder_id_by_name("non_existent", "parent_id")
    end_time = time.perf_counter()

    # We want to capture the output of get_folder_id_by_name to avoid printing thousands of lines
    # But for benchmark we just want the time.

    print(f"Time taken for {num_children} children: {end_time - start_time:.6f} seconds")

if __name__ == "__main__":
    # Redirect stdout to devnull during benchmark to avoid flooding the console with debug prints
    # which might affect the benchmark itself.
    original_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    try:
        benchmark()
    finally:
        sys.stdout.close()
        sys.stdout = original_stdout
        # Re-run once to see the time
        import io
        output = io.StringIO()
        sys.stdout = output
        benchmark()
        sys.stdout = original_stdout
        print(output.getvalue())
