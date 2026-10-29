import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_FOOTBALL_KEY")

url = "https://v3.football.api-sports.io/fixtures"
headers = {
    "x-apisports-key": api_key
}
params = {
    "id": 1208150,
    "timezone": "Asia/Seoul"
}

response = requests.get(url, headers=headers, params=params)
data = response.json()
match = data["response"][0]

print("에러:", data["errors"])
print()

# 1. 명단 (선발 / 벤치)
for team in match["lineups"]:
    print("=====", team["team"]["name"], "(", team["formation"], ") =====")

    print("[선발]")
    for p in team["startXI"]:
        print(" ", p["player"]["number"], p["player"]["name"], "- id:", p["player"]["id"])

    print("[벤치]")
    for p in team["substitutes"]:
        print(" ", p["player"]["number"], p["player"]["name"], "- id:", p["player"]["id"])
    print()

# 2. 경기 이벤트 (골, 교체만)
print("===== 이벤트 =====")
for e in match["events"]:
    minute = e["time"]["elapsed"]
    team_name = e["team"]["name"]
    player = e["player"]["name"]
    assist = e["assist"]["name"]

    if e["type"] == "Goal":
        print(minute, "분 [골]", team_name, "-", player, "/ 도움:", assist)

    if e["type"] == "subst":
        print(minute, "분 [교체]", team_name, "- player:", player, "/ assist:", assist)