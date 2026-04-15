import sys
from unittest.mock import MagicMock

# Mock requests before importing create_worklog
# Since requests is not available in the environment, we mock it.
mock_requests = MagicMock()
class MockHTTPError(Exception):
    pass
mock_requests.exceptions.HTTPError = MockHTTPError
sys.modules["requests"] = mock_requests

import unittest
from unittest.mock import patch, Mock
from datetime import datetime
import os

# 테스트를 위한 더미 환경 변수 설정
os.environ["BASE_URL"] = "https://test.atlassian.net/wiki/rest/api"
os.environ["BASE_URL_V1"] = "https://test.atlassian.net/wiki/rest/api/v1"
os.environ["SPACE_ID"] = "12345"
os.environ["TEMPLATE_ID"] = "67890"
os.environ["ROOT_FOLDER_ID"] = "111213"
os.environ["ATLASSIAN_USER"] = "test@example.com"
os.environ["ATLASSIAN_API_TOKEN"] = "test_token"

import sys
from unittest.mock import MagicMock

# Mock requests before importing create_worklog
mock_requests = MagicMock()
# Add a mock HTTPError to the mock_requests
class MockHTTPError(Exception):
    pass
mock_requests.exceptions.HTTPError = MockHTTPError
sys.modules["requests"] = mock_requests

# requests가 import되기 전에 환경 변수가 설정되었는지 확인하기 위해 여기서 import합니다.
import create_worklog

class TestCreateWorklog(unittest.TestCase):
    def setUp(self):
        # Clear cache before each test
        create_worklog._FOLDER_CACHE = {}

    @patch('create_worklog.requests.get')
    def test_get_folder_id_by_name_found(self, mock_get):
        # 폴더를 찾았을 때의 API 응답을 모의 처리합니다.
        mock_response = Mock()
        mock_response.json.return_value = {
            "directChildren": {
                "results": [
                    {"title": "other_folder", "id": "1"},
                    {"title": "target_folder", "id": "123"}
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        folder_id = create_worklog.get_folder_id_by_name("target_folder", "parent_id")
        self.assertEqual(folder_id, "123")
        mock_get.assert_called_once_with(
            "https://test.atlassian.net/wiki/rest/api/folders/parent_id?include-direct-children=true",
            auth=("test@example.com", "test_token"),
            headers={"Accept": "application/json"},
            timeout=10
        )

    @patch('create_worklog.requests.get')
    def test_get_folder_id_by_name_not_found(self, mock_get):
        # 폴더를 찾지 못했을 때의 API 응답을 모의 처리합니다.
        mock_response = Mock()
        mock_response.json.return_value = {
            "directChildren": {
                "results": [
                    {"title": "other_folder", "id": "1"}
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        folder_id = create_worklog.get_folder_id_by_name("target_folder", "parent_id")
        self.assertIsNone(folder_id)

    @patch('create_worklog.requests.get')
    def test_get_folder_id_by_name_api_error(self, mock_get):
        # API 오류가 발생했을 때의 응답을 모의 처리합니다.
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = mock_requests.exceptions.HTTPError
        mock_get.return_value = mock_response

        with self.assertRaises(mock_requests.exceptions.HTTPError):
            create_worklog.get_folder_id_by_name("target_folder", "parent_id")

    @patch('create_worklog.get_folder_id_by_name', return_value="existing_folder_id")
    def test_find_or_create_folder_exists(self, mock_get_folder):
        folder_id = create_worklog.find_or_create_folder("existing_folder", "parent")
        self.assertEqual(folder_id, "existing_folder_id")
        mock_get_folder.assert_called_once_with("existing_folder", "parent")

    @patch('create_worklog.get_folder_id_by_name', return_value=None)
    @patch('create_worklog.requests.post')
    def test_find_or_create_folder_create_success(self, mock_post, mock_get_folder):
        # 폴더 생성 성공 시의 API 응답을 모의 처리합니다.
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "new_folder_id"}
        mock_post.return_value = mock_response

        folder_id = create_worklog.find_or_create_folder("new_folder", "parent")
        self.assertEqual(folder_id, "new_folder_id")
        mock_get_folder.assert_called_once_with("new_folder", "parent")
        mock_post.assert_called_once()

    @patch('create_worklog.get_folder_id_by_name', return_value=None)
    @patch('create_worklog.requests.post')
    def test_find_or_create_folder_create_fail(self, mock_post, mock_get_folder):
        # 실패한 API 응답을 모의 처리합니다.
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = mock_requests.exceptions.HTTPError("HTTP Error")
        mock_post.return_value = mock_response

        with self.assertRaises(mock_requests.exceptions.HTTPError):
            create_worklog.find_or_create_folder("fail_folder", "parent")

    @patch('create_worklog.requests.post')
    def test_create_page_success(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "new_page_id"}
        mock_post.return_value = mock_response

        page_id = create_worklog.create_page("test_page", "parent", "body")
        self.assertEqual(page_id, "new_page_id")

    @patch('create_worklog.requests.post')
    def test_create_page_already_exists(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        page_id = create_worklog.create_page("existing_page", "parent", "body")
        self.assertIsNone(page_id)

    @patch('create_worklog.requests.get')
    def test_get_template_body(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {"body": {"storage": {"value": "template_body_content"}}}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        body = create_worklog.get_template_body()
        self.assertEqual(body, "template_body_content")
        mock_get.assert_called_once_with(
            "https://test.atlassian.net/wiki/rest/api/v1/template/67890",
            auth=("test@example.com", "test_token"),
            headers={"Accept": "application/json"},
            timeout=10
        )

    # --- Weekday Logic Tests ---
    # Note: create_worklog.main replaces the specific string "2025-08-07" in the template body.

    @patch('create_worklog.create_page')
    @patch('create_worklog.get_template_body', return_value='template body with 2025-08-07')
    @patch('create_worklog.find_or_create_folder')
    def test_main_logic_on_monday_does_not_create_page(self, mock_find_folder, mock_get_body, mock_create_page):
        # 월요일 (0)
        monday = datetime(2025, 6, 9)
        create_worklog.main(monday)
        mock_create_page.assert_not_called()
    @patch('create_worklog.requests.get')
    def test_get_template_body_error(self, mock_get):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = mock_requests.exceptions.HTTPError
        mock_get.return_value = mock_response

        with self.assertRaises(mock_requests.exceptions.HTTPError):
            create_worklog.get_template_body()

    @patch('create_worklog.create_page')
    @patch('create_worklog.get_template_body', return_value='template body with 2025-08-07')
    @patch('create_worklog.find_or_create_folder')
    def test_main_logic_on_tuesday_creates_page(self, mock_find_folder, mock_get_body, mock_create_page):
        # 화요일 (1)
        mock_find_folder.side_effect = lambda name, parent: f"id_{name}"
        tuesday = datetime(2025, 6, 10)
        create_worklog.main(tuesday)

        mock_create_page.assert_called_once_with(
            '06_12_워크로그',
            'id_2025_06',
            'template body with 2025-06-12'
        )

    @patch('create_worklog.create_page')
    @patch('create_worklog.get_template_body', return_value='template body with 2025-08-07')
    @patch('create_worklog.find_or_create_folder')
    def test_main_logic_on_wednesday_creates_page(self, mock_find_folder, mock_get_body, mock_create_page):
        # 수요일 (2)
        mock_find_folder.side_effect = lambda name, parent: f"id_{name}"
        wednesday = datetime(2025, 6, 11)
        create_worklog.main(wednesday)

        mock_create_page.assert_called_once_with(
            '06_12_워크로그',
            'id_2025_06',
            'template body with 2025-06-12'
        )

    @patch('create_worklog.create_page')
    @patch('create_worklog.get_template_body', return_value='template body with 2025-08-07')
    @patch('create_worklog.find_or_create_folder')
    def test_main_logic_on_thursday_creates_page(self, mock_find_folder, mock_get_body, mock_create_page):
        # 목요일 (3)
        mock_find_folder.side_effect = lambda name, parent: f"id_{name}"
        thursday = datetime(2025, 6, 12)
        create_worklog.main(thursday)

        mock_create_page.assert_called_once_with(
            '06_12_워크로그',
            'id_2025_06',
            'template body with 2025-06-12'
        )

    @patch('create_worklog.create_page')
    @patch('create_worklog.get_template_body', return_value='template body with 2025-08-07')
    @patch('create_worklog.find_or_create_folder')
    def test_main_logic_on_friday_does_not_create_page(self, mock_find_folder, mock_get_body, mock_create_page):
        # 금요일 (4)
        friday = datetime(2025, 6, 13)
        create_worklog.main(friday)
        mock_create_page.assert_not_called()

    @patch('create_worklog.create_page')
    @patch('create_worklog.get_template_body', return_value='template body with 2025-08-07')
    @patch('create_worklog.find_or_create_folder')
    def test_main_logic_on_saturday_does_not_create_page(self, mock_find_folder, mock_get_body, mock_create_page):
        # 토요일 (5)
        saturday = datetime(2025, 6, 14)
        create_worklog.main(saturday)
        mock_create_page.assert_not_called()

    @patch('create_worklog.create_page')
    @patch('create_worklog.get_template_body', return_value='template body with 2025-08-07')
    @patch('create_worklog.find_or_create_folder')
    def test_main_logic_on_sunday_does_not_create_page(self, mock_find_folder, mock_get_body, mock_create_page):
        # 일요일 (6)
        sunday = datetime(2025, 6, 15)
        create_worklog.main(sunday)
        mock_create_page.assert_not_called()

    @patch('create_worklog.create_page')
    @patch('create_worklog.get_template_body', return_value='template body with 2025-08-07')
    @patch('create_worklog.find_or_create_folder')
    def test_main_logic_month_transition(self, mock_find_folder, mock_get_body, mock_create_page):
        # 화요일 9월 30일 -> 목요일 10월 2일
        mock_find_folder.side_effect = lambda name, parent: f"id_{name}"
        tue_sep_30 = datetime(2025, 9, 30)
        create_worklog.main(tue_sep_30)

        mock_create_page.assert_called_once_with(
            '10_02_워크로그',
            'id_2025_10',
            'template body with 2025-10-02'
        )

    # --- Other tests ---

    @patch('create_worklog.create_page')
    @patch('create_worklog.get_template_body')
    @patch('create_worklog.find_or_create_folder')
    def test_main_logic_end_of_month(self, mock_find_folder, mock_get_body, mock_create_page):
        # 28일에 다음 달 폴더가 생성되는지 테스트합니다.
        test_date = datetime(2025, 5, 28)

        folder_ids = {
            ('2025_워크로그', '111213'): 'year_folder',
            ('2025_05', 'year_folder'): 'month_folder',
            ('2025_06', 'year_folder'): 'next_month_folder'
        }
        mock_find_folder.side_effect = lambda name, parent: folder_ids.get((name, parent), 'default_folder_id')

        create_worklog.main(test_date)

        mock_find_folder.assert_any_call('2025_06', 'year_folder')

    @patch('create_worklog.create_page')
    @patch('create_worklog.get_template_body')
    @patch('create_worklog.find_or_create_folder')
    def test_main_logic_end_of_year(self, mock_find_folder, mock_get_body, mock_create_page):
        # 12월 28일에 다음 해와 다음 달 폴더가 생성되는지 테스트합니다.
        test_date = datetime(2025, 12, 28)

        folder_ids = {
            ('2025_워크로그', '111213'): '2025_year_folder',
            ('2025_12', '2025_year_folder'): '2025_12_month_folder',
            ('2026_워크로그', '111213'): '2026_year_folder',
            ('2026_01', '2026_year_folder'): '2026_01_month_folder',
        }
        mock_find_folder.side_effect = lambda name, parent: folder_ids.get((name, parent))

        create_worklog.main(test_date)

        mock_find_folder.assert_any_call('2026_워크로그', '111213')
        mock_find_folder.assert_any_call('2026_01', '2026_year_folder')

if __name__ == '__main__':
    unittest.main()
