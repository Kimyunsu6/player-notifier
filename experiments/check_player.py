import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_FOOTBALL_KEY")

PLAYER_ID = 328089         # 손흥민
FIXTURE_ID = 1208150    # 토트넘 vs 풀럼
file_name = "sample_" + str(FIXTURE_ID) + ".json"

# 1. 경기 데이터 가져오기 (파일이 있으면 파일에서, 없으면 API에서)
if os.path.exists(file_name):
    print("(저장된 파일에서 읽음)")
    with open(file_name, "r", encoding="utf-8") as f:
        match = json.load(f)
else:
    print("(API에서 받아옴)")
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": api_key}
    params = {"id": FIXTURE_ID, "timezone": "Asia/Seoul"}
    response = requests.get(url, headers=headers, params=params)
    match = response.json()["response"][0]
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(match, f, ensure_ascii=False, indent=2)

# 2. 선발 / 벤치 / 명단 제외 판단
status = "명단 제외"
player_name = ""
team_name = ""

for team in match["lineups"]:
    for p in team["startXI"]:
        if p["player"]["id"] == PLAYER_ID:
            status = "선발"
            player_name = p["player"]["name"]
            team_name = team["team"]["name"]
    for p in team["substitutes"]:
        if p["player"]["id"] == PLAYER_ID:
            status = "벤치"
            player_name = p["player"]["name"]
            team_name = team["team"]["name"]

print("선수:", player_name, "/", team_name)
print("명단:", status)

# 3. 이벤트 확인 (교체, 골, 도움)
was_bench = (status == "벤치")

for e in match["events"]:
    minute = e["time"]["elapsed"]
    p_id = e["player"]["id"]
    a_id = e["assist"]["id"]

    # 교체
    if e["type"] == "subst":
        if p_id == PLAYER_ID or a_id == PLAYER_ID:
            # 상대 선수 이름 찾기
            if p_id == PLAYER_ID:
                other = e["assist"]["name"]
            else:
                other = e["player"]["name"]

            if was_bench:
                print(minute, "분 교체 투입 (", other, "대신 )")
                was_bench = False   # 이제 경기에 들어간 상태
            else:
                print(minute, "분 교체 아웃 (", other, "투입 )")

    # 골 / 도움
    if e["type"] == "Goal" and e["detail"] != "Missed Penalty":
        if p_id == PLAYER_ID and e["detail"] != "Own Goal":
            print(minute, "분 골!")
        if a_id == PLAYER_ID:
            print(minute, "분 도움!")