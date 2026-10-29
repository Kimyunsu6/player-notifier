import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

PLAYER_ID = 19025         # 손흥민
FIXTURE_ID = 1208150
file_name = "sample_" + str(FIXTURE_ID) + ".json"

with open(file_name, "r", encoding="utf-8") as f:
    match = json.load(f)


# null(None)이면 0으로 바꾸는 함수
def num(value):
    if value is None:
        return 0
    return int(value)


# 성공률을 막대로 바꾸는 함수 (예: 84% -> ▰▰▰▰▱)
def make_bar(percent):
    filled = round(percent / 20)
    return "▰" * filled + "▱" * (5 - filled)


# ---------- 1. 내 선수 기록 찾기 ----------
stats = None
for team in match["players"]:
    for p in team["players"]:
        if p["player"]["id"] == PLAYER_ID:
            stats = p["statistics"][0]
            player_name = p["player"]["name"]
            team_name = team["team"]["name"]
            team_logo = team["team"]["logo"]

if stats is None or num(stats["games"]["minutes"]) == 0:
    print("출전 기록 없음 - 알림 없음")
    exit()

# ---------- 2. 숫자 정리 ----------
rating = float(stats["games"]["rating"])
minutes = num(stats["games"]["minutes"])
goals = num(stats["goals"]["total"])
assists = num(stats["goals"]["assists"])
shots = num(stats["shots"]["total"])
shots_on = num(stats["shots"]["on"])
pass_total = num(stats["passes"]["total"])
pass_ok = num(stats["passes"]["accuracy"])   # 성공 횟수
key_pass = num(stats["passes"]["key"])
duel_total = num(stats["duels"]["total"])
duel_won = num(stats["duels"]["won"])

# 성공률 계산 (0으로 나누기 방지)
if pass_total > 0:
    pass_pct = round(pass_ok / pass_total * 100)
else:
    pass_pct = 0

if duel_total > 0:
    duel_pct = round(duel_won / duel_total * 100)
else:
    duel_pct = 0

# ---------- 3. 평점별 색상, 한 줄 평가 ----------
if rating >= 9.0:
    color = 0x1E88E5
    comment_ko = "경기를 지배한 활약"
    comment_en = "World-class display."
elif rating >= 8.0:
    color = 0x1E8E3E
    comment_ko = "경기 최고 수준의 활약"
    comment_en = "Outstanding performance."
elif rating >= 7.0:
    color = 0x34A853
    comment_ko = "좋은 활약"
    comment_en = "Strong performance."
elif rating >= 6.0:
    color = 0xF29900
    comment_ko = "무난한 경기"
    comment_en = "Steady performance."
else:
    color = 0xD93025
    comment_ko = "아쉬운 경기"
    comment_en = "Below par."

# 추가 칭찬 조건
extra_ko = []
extra_en = []
if goals + assists >= 1:
    extra_ko.append("공격 포인트 기록")
    extra_en.append("direct goal contribution")
if pass_total >= 20 and pass_pct >= 90:
    extra_ko.append("정확한 패스")
    extra_en.append("accurate passing")
if key_pass >= 3:
    extra_ko.append("찬스 메이킹")
    extra_en.append("creative threat")
if duel_total >= 5 and duel_pct >= 60:
    extra_ko.append("경합 우위")
    extra_en.append("won his duels")

if len(extra_ko) > 0:
    comment_ko = comment_ko + " · " + ", ".join(extra_ko)
    comment_en = comment_en + " Highlights: " + ", ".join(extra_en) + "."

# ---------- 4. 경기 결과 ----------
home = match["teams"]["home"]["name"]
away = match["teams"]["away"]["name"]
score = str(match["goals"]["home"]) + "-" + str(match["goals"]["away"])
league_name = match["league"]["name"]

# ---------- 5. 임베드 만들기 ----------
embed = {
    "author": {"name": team_name, "icon_url": team_logo},
    "title": "FULL TIME  ·  평점 " + str(rating),
    "description": "**" + player_name + "**\n" + home + " " + score + " " + away,
    "color": color,
    "thumbnail": {"url": "https://media.api-sports.io/football/players/" + str(PLAYER_ID) + ".png"},
    "fields": [
        {"name": "출전 시간", "value": str(minutes) + "분", "inline": True},
        {"name": "골 / 도움", "value": str(goals) + " / " + str(assists), "inline": True},
        {"name": "슈팅 (유효)", "value": str(shots) + " (" + str(shots_on) + ")", "inline": True},
        {"name": "패스 성공", "value": str(pass_ok) + "/" + str(pass_total) + "  " + str(pass_pct) + "%\n" + make_bar(pass_pct), "inline": True},
        {"name": "키패스", "value": str(key_pass), "inline": True},
        {"name": "경합 승리", "value": str(duel_won) + "/" + str(duel_total) + "  " + str(duel_pct) + "%\n" + make_bar(duel_pct), "inline": True},
        {"name": "평가", "value": comment_ko + "\n*" + comment_en + "*", "inline": False}
    ],
    "footer": {"text": league_name}
}

response = requests.post(webhook_url, json={"embeds": [embed]})
print("응답 코드:", response.status_code)