import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_FOOTBALL_KEY")
webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

PLAYER_ID = 186       # 캐어니 (테스트용)
FIXTURE_ID = 1208150    # 토트넘 vs 풀럼
file_name = "sample_" + str(FIXTURE_ID) + ".json"

# ---------- 1. 경기 데이터 가져오기 ----------
if os.path.exists(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        match = json.load(f)
else:
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": api_key}
    params = {"id": FIXTURE_ID, "timezone": "Asia/Seoul"}
    response = requests.get(url, headers=headers, params=params)
    match = response.json()["response"][0]
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(match, f, ensure_ascii=False, indent=2)

# ---------- 2. 경기 기본 정보 ----------
home_name = match["teams"]["home"]["name"]
away_name = match["teams"]["away"]["name"]
kickoff = match["fixture"]["date"][:16].replace("T", " ")
league_name = match["league"]["name"]
league_logo = match["league"]["logo"]
photo_url = "https://media.api-sports.io/football/players/" + str(PLAYER_ID) + ".png"

# ---------- 3. 디스코드로 임베드 보내는 함수 ----------
def send_embed(title, description, color):
    embed = {
        "title": title,
        "description": description,
        "color": color,
        "thumbnail": {"url": photo_url},
        "footer": {"text": league_name, "icon_url": league_logo}
    }
    response = requests.post(webhook_url, json={"embeds": [embed]})
    print("전송:", title, "/ 응답 코드:", response.status_code)
    time.sleep(1)   # 너무 빨리 보내지 않게 1초 쉬기

# ---------- 4. 선발 / 벤치 판단 ----------
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

# 상대팀 찾기
if team_name == home_name:
    opponent = away_name
else:
    opponent = home_name

match_info = "vs " + opponent + "\n킥오프 " + kickoff

# 명단 알림
if status == "선발":
    send_embed("🟢 선발 출전", "**" + player_name + "** (" + team_name + ")\n" + match_info, 0x2ECC71)
elif status == "벤치":
    send_embed("🪑 벤치 대기", "**" + player_name + "** (" + team_name + ")\n" + match_info, 0x95A5A6)
else:
    print("명단 제외 - 알림 없음")

# ---------- 5. 이벤트 알림 (교체, 골, 도움) ----------
was_bench = (status == "벤치")

for e in match["events"]:
    minute = str(e["time"]["elapsed"])
    p_id = e["player"]["id"]
    a_id = e["assist"]["id"]

    # 교체
    if e["type"] == "subst":
        if p_id == PLAYER_ID or a_id == PLAYER_ID:
            if p_id == PLAYER_ID:
                other = e["assist"]["name"]
            else:
                other = e["player"]["name"]

            if was_bench:
                send_embed("🔄 교체 투입", "**" + player_name + "**\n" + minute + "분, " + other + " 대신 투입", 0x3498DB)
                was_bench = False
            else:
                print(minute, "분 교체 아웃 (알림 없음)")

    # 골 / 도움
    if e["type"] == "Goal" and e["detail"] != "Missed Penalty":
        if p_id == PLAYER_ID and e["detail"] != "Own Goal":
            send_embed("⚽ 골!", "**" + player_name + "**\n" + minute + "분 득점", 0xF1C40F)
        if a_id == PLAYER_ID:
            send_embed("🅰️ 도움!", "**" + player_name + "**\n" + minute + "분 도움", 0xE67E22)