import os
import json
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

PLAYER_ID = "140033"    # Tom Cairney (테스트용)
EVENT_ID = 704401       # 토트넘 vs 풀럼
file_name = "sample_espn_" + str(EVENT_ID) + ".json"


# "62'" -> 62, "90'+5'" -> 95
def to_minute(text):
    text = text.replace("'", "")
    if "+" in text:
        parts = text.split("+")
        return int(parts[0]) + int(parts[1])
    return int(text)


# "WWDLL" -> "승승무패패"
def form_ko(text):
    text = text.replace("W", "승")
    text = text.replace("D", "무")
    text = text.replace("L", "패")
    return text


with open(file_name, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- 1. 내 선수 찾기 ----------
status = "명단 제외"
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

if status == "명단 제외":
    print("명단 제외 - 알림 없음")
    exit()

# ---------- 2. 경기 정보 (header) ----------
competition = data["header"]["competitions"][0]
for c in competition["competitors"]:
    if c["team"]["id"] == team_id:
        my = c
    else:
        opp = c

opponent = opp["team"]["displayName"]

if my["homeAway"] == "home":
    home_away = "홈"
else:
    home_away = "원정"

# 킥오프 시간: UTC -> 한국 시간
utc_time = datetime.strptime(competition["date"], "%Y-%m-%dT%H:%MZ")
kst_time = utc_time + timedelta(hours=9)
kickoff = kst_time.strftime("%m.%d %H:%M")

# 시즌 성적 (승-무-패, 승점)
record = my["record"][0]["summary"] + " · " + my["record"][1]["summary"] + "점"

# 최근 5경기
my_form = my["team"]["abbreviation"] + "  " + form_ko(my["team"]["form"])
opp_form = opp["team"]["abbreviation"] + "  " + form_ko(opp["team"]["form"])

league_name = my["team"]["groups"]["name"]
color = int(team_color, 16)     # "0B1426" -> 숫자


# ---------- 3. 디스코드 임베드 보내기 ----------
def send_embed(title, description, fields):
    embed = {
        "author": {"name": team_name},
        "title": title,
        "description": description,
        "color": color,
        "thumbnail": {"url": team_logo},
        "fields": fields,
        "footer": {"text": league_name}
    }
    response = requests.post(webhook_url, json={"embeds": [embed]})
    print("전송:", title, "/ 응답 코드:", response.status_code)
    time.sleep(1)


# ---------- 4. 명단 알림 ----------
if status == "선발":
    title = "STARTING XI"
else:
    title = "ON THE BENCH"

lineup_fields = [
    {"name": "킥오프", "value": kickoff, "inline": True},
    {"name": "홈/원정", "value": home_away, "inline": True},
    {"name": "시즌 성적", "value": record, "inline": True},
    {"name": "최근 5경기", "value": my_form + "\n" + opp_form, "inline": False}
]
send_embed(title, "**" + player_name + "**\nvs " + opponent, lineup_fields)

# ---------- 5. 이벤트 알림 ----------
was_bench = (status == "벤치")

for ke in data["keyEvents"]:
    event_type = ke["type"]["type"]
    event_text = ke["type"]["text"]
    minute_text = ke["clock"]["displayValue"]
    if minute_text == "":
        continue

    ids = []
    names = []
    for part in ke.get("participants", []):
        ids.append(part["athlete"]["id"])
        names.append(part["athlete"]["displayName"])

    # 교체 투입
    if event_type == "substitution" and PLAYER_ID in ids:
        if ids[0] == PLAYER_ID:
            other = names[1]
        else:
            other = names[0]
        if was_bench:
            send_embed("SUB ON  " + minute_text, "**" + player_name + "**\n" + other + " 대신 투입", [])
            was_bench = False

    # 골 / 도움
    if ke.get("scoringPlay") == True and len(ids) > 0:
        if ids[0] == PLAYER_ID and "Own Goal" not in event_text:
            send_embed("GOAL  " + minute_text, "**" + player_name + "**", [])
        if len(ids) > 1 and ids[1] == PLAYER_ID:
            send_embed("ASSIST  " + minute_text, "**" + player_name + "**", [])

    # 퇴장
    if "Red Card" in event_text and len(ids) > 0 and ids[0] == PLAYER_ID:
        send_embed("RED CARD  " + minute_text, "**" + player_name + "**", [])