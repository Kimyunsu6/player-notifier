import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

PLAYER_ID = "328050"    # Tom Cairney (테스트용)
EVENT_ID = 704401       # 토트넘 vs 풀럼
file_name = "sample_espn_" + str(EVENT_ID) + ".json"


# "62'" -> 62, "90'+5'" -> 95
def to_minute(text):
    text = text.replace("'", "")
    if "+" in text:
        parts = text.split("+")
        return int(parts[0]) + int(parts[1])
    return int(text)


with open(file_name, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- 1. 내 선수 찾기 + 스탯 정리 ----------
status = "명단 제외"
stat = {}       # 스탯 이름 -> 숫자 (예: stat["totalGoals"] = 1)

for team in data["rosters"]:
    for p in team["roster"]:
        if p["athlete"]["id"] == PLAYER_ID:
            player_name = p["athlete"]["displayName"]
            team_id = team["team"]["id"]
            team_name = team["team"]["displayName"]
            team_logo = team["team"]["logos"][0]["href"]
            team_color = team["team"]["alternateColor"]
            if p["starter"] == True:
                status = "선발"
            else:
                status = "벤치"
            for s in p.get("stats", []):
                stat[s["name"]] = int(s["value"])

if status == "명단 제외":
    print("명단 제외 - 리포트 없음")
    exit()

# ---------- 2. 경기 흐름 + 출전 시간 ----------
was_bench = (status == "벤치")
played = (status == "선발")    # 실제로 뛰었는지
in_minute = 0
out_minute = 90
timeline = []                   # 예: ["62' 투입", "67' 골"]

for ke in data["keyEvents"]:
    event_type = ke["type"]["type"]
    event_text = ke["type"]["text"]
    minute_text = ke["clock"]["displayValue"]
    if minute_text == "":
        continue

    ids = []
    for part in ke.get("participants", []):
        ids.append(part["athlete"]["id"])

    if PLAYER_ID not in ids:
        continue                # 내 선수와 관계없는 이벤트는 건너뛰기

    # 교체
    if event_type == "substitution":
        if was_bench:
            timeline.append(minute_text + " 투입")
            in_minute = to_minute(minute_text)
            was_bench = False
            played = True
        else:
            timeline.append(minute_text + " 교체 아웃")
            out_minute = to_minute(minute_text)

    # 골 / 도움
    if ke.get("scoringPlay") == True:
        if ids[0] == PLAYER_ID and "Own Goal" not in event_text:
            timeline.append(minute_text + " 골")
        if len(ids) > 1 and ids[1] == PLAYER_ID:
            timeline.append(minute_text + " 도움")

    # 카드
    if "Yellow Card" in event_text and ids[0] == PLAYER_ID:
        timeline.append(minute_text + " 경고")
    if "Red Card" in event_text and ids[0] == PLAYER_ID:
        timeline.append(minute_text + " 퇴장")
        out_minute = to_minute(minute_text)

if played == False:
    print("미출전 - 리포트 없음")
    exit()

minutes = out_minute - in_minute

if len(timeline) == 0:
    flow = "특이 사항 없음"
else:
    flow = " → ".join(timeline)

# ---------- 3. 최종 스코어 ----------
competition = data["header"]["competitions"][0]
for c in competition["competitors"]:
    if c["homeAway"] == "home":
        home_name = c["team"]["displayName"]
        home_score = c["score"]
    else:
        away_name = c["team"]["displayName"]
        away_score = c["score"]

final_score = home_name + " " + home_score + "-" + away_score + " " + away_name
league_name = competition["competitors"][0]["team"]["groups"]["name"]

# ---------- 4. 임베드 만들기 ----------
# 스탯이 없으면 0으로 (stat.get(이름, 0))
fields = [
    {"name": "출전 시간", "value": str(minutes) + "분", "inline": True},
    {"name": "골 / 도움", "value": str(stat.get("totalGoals", 0)) + " / " + str(stat.get("goalAssists", 0)), "inline": True},
    {"name": "슈팅 (유효)", "value": str(stat.get("totalShots", 0)) + " (" + str(stat.get("shotsOnTarget", 0)) + ")", "inline": True},
    {"name": "파울 유도", "value": str(stat.get("foulsSuffered", 0)), "inline": True},
    {"name": "파울", "value": str(stat.get("foulsCommitted", 0)), "inline": True},
    {"name": "경고 / 퇴장", "value": str(stat.get("yellowCards", 0)) + " / " + str(stat.get("redCards", 0)), "inline": True},
    {"name": "경기 흐름", "value": flow, "inline": False}
]

embed = {
    "author": {"name": team_name},
    "title": "FULL TIME",
    "description": "**" + player_name + "**\n" + final_score,
    "color": int(team_color, 16),
    "thumbnail": {"url": team_logo},
    "fields": fields,
    "footer": {"text": league_name}
}

response = requests.post(webhook_url, json={"embeds": [embed]})
print("응답 코드:", response.status_code)