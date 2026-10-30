import json
import time
import requests

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/"
LEAGUES = {
    "eng.1": "프리미어리그",
    "esp.1": "라리가",
    "ita.1": "세리에A",
    "ger.1": "분데스리가"
}

players = []

for league in LEAGUES:
    print("리그:", LEAGUES[league])
    teams_data = requests.get(BASE_URL + league + "/teams").json()
    teams = teams_data["sports"][0]["leagues"][0]["teams"]

    for t in teams:
        team = t["team"]
        roster = requests.get(BASE_URL + league + "/teams/" + team["id"] + "/roster").json()

        count = 0
        for a in roster.get("athletes", []):
            players.append({
                "id": a["id"],
                "name": a.get("displayName", ""),
                "team_id": team["id"],
                "team": team["displayName"],
                "league": league
            })
            count = count + 1

        print("  ", team["displayName"], count, "명")
        time.sleep(0.2)     # ESPN에 너무 빨리 요청하지 않기

# 파일로 저장 (한 줄로 저장해서 용량 줄이기)
with open("player_db.json", "w", encoding="utf-8") as f:
    json.dump(players, f, ensure_ascii=False)

print()
print("완료: 선수", len(players), "명 저장")