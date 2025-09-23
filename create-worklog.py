import os
import requests
from datetime import datetime, timedelta

BASE_URL = os.environ["BASE_URL"]
BASE_URL_V1 = os.environ["BASE_URL_V1"]
SPACE_ID = os.environ["SPACE_ID"]
TEMPLATE_ID = os.environ["TEMPLATE_ID"]
ROOT_FOLDER_ID = os.environ["ROOT_FOLDER_ID"]
AUTH = (os.environ["ATLASSIAN_USER"], os.environ["ATLASSIAN_API_TOKEN"])


def get_folder_id_by_name(name, parent_id):
    # parentId 하위 폴더 조회
    url = f"{BASE_URL}/folders/{parent_id}?include-direct-children=true"
    headers = {"Accept": "application/json"}
    r = requests.get(url, auth=AUTH, headers=headers)
    r.raise_for_status()
    data = r.json()

    children = data.get("directChildren", {}).get("results", [])
    print(f"[DEBUG] Folders under parent={parent_id}: {[c.get('title') for c in children]}")

    for f in children:
        if f.get("title") == name:
            print(f"[FOUND] Folder exists: {name} (id={f['id']})")
            return f["id"]

    return None

def find_or_create_folder(name, parent_id):
    # 1. 먼저 조회
    folder_id = get_folder_id_by_name(name, parent_id)
    if folder_id:
        return folder_id

    # 2. 없으면 생성
    url = f"{BASE_URL}/folders"
    payload = {"spaceId": SPACE_ID, "title": name, "parentId": parent_id}

    r = requests.post(url, auth=AUTH, json=payload)
    if r.status_code in (200, 201):
        data = r.json()
        print(f"[CREATE] Folder created: {name} (id={data['id']})")
        return data["id"]
    else:
        print(f"[ERROR] Failed to create folder: {name}, status={r.status_code}, body={r.text}")
        r.raise_for_status()

def create_page(title, parent_id, body):
    url = f"{BASE_URL}/pages"
    data = {
        "spaceId": SPACE_ID,
        "title": title,
        "parentId": parent_id,
        "status": "current",
        "position": 0,
        "body": {
            "representation": "storage",
            "value": body
        },
        "subtype": "live"
    }

    r = requests.post(url, auth=AUTH, json=data)
    if r.status_code == 409:  # 이미 존재
        print(f"[SKIP] Page already exists: {title}")
        return None
    r.raise_for_status()
    page_id = r.json()["id"]
    print(f"[CREATE] Page created: {title} (id={page_id})")
    return page_id

def get_template_body():
    url = f"{BASE_URL_V1}/template/{TEMPLATE_ID}"  # v1 API
    headers = {"Accept": "application/json"}
    r = requests.get(url, auth=AUTH, headers=headers)
    r.raise_for_status()
    data = r.json()
    return data["body"]["storage"]["value"]

if __name__ == "__main__":
    today = datetime.today()
    print(f"===== Confluence Automation Start: {today.strftime('%Y-%m-%d (%A)')} =====")

    # 메인 연도 폴더 (올해)
    year_folder_name = f"{today.year}_워크로그"
    year_folder_id = find_or_create_folder(year_folder_name, ROOT_FOLDER_ID)

    # 이번 달 폴더
    month_folder_name = f"{today.year}_{today.strftime('%m')}"
    month_folder_id = find_or_create_folder(month_folder_name, year_folder_id)

    # 1. 매년 12/28 이후 → 내년 폴더 생성
    if today.month == 12 and today.day >= 28:
        next_year_folder_name = f"{today.year + 1}_워크로그"
        find_or_create_folder(next_year_folder_name, ROOT_FOLDER_ID)
        print(f"[TASK] Next year folder checked: {next_year_folder_name}")

    # 2. 매월 28일 이후 → 다음 달 폴더 생성
    if today.day >= 28:
        next_month = today.month % 12 + 1
        next_year = today.year + (1 if next_month == 1 else 0)
        next_month_folder_name = f"{next_year}_{str(next_month).zfill(2)}"
        next_year_folder_id = find_or_create_folder(f"{next_year}_워크로그", ROOT_FOLDER_ID)
        find_or_create_folder(next_month_folder_name, next_year_folder_id)
        print(f"[TASK] Next month folder checked: {next_month_folder_name}")

    # 3. 매주 화, 수, 목 → 목요일 워크로그 생성
    if today.weekday() in [1, 2, 3]:
        thursday = today + timedelta(days=(3 - today.weekday()))
        page_title = f"{thursday.strftime('%m_%d')}_워크로그"
        formatted_date = thursday.strftime("%Y-%m-%d")  # 예: 2025년 9월 11일

        # 템플릿 본문 불러오기
        body = get_template_body()

        # 날짜 치환 (기존 템플릿에 박혀있는 "2025년 8월 7일" → 새 날짜)
        updated_body = body.replace("2025-08-07", formatted_date)

        # 페이지 생성
        page_id = create_page(page_title, month_folder_id, updated_body)

        print(f"Created and updated page: {page_title} ({formatted_date}) id={page_id}")