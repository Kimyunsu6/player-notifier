import json

EVENT_ID = 704401
file_name = "sample_espn_" + str(EVENT_ID) + ".json"

with open(file_name, "r", encoding="utf-8") as f:
    data = json.load(f)

# 1. 첫 번째 팀의 첫 경기 하나를 통째로 보기 (구조 확인용)
first_team = data["lastFiveGames"][0]
print("===== 구조 확인 =====")
print("항목 이름:", list(first_team.keys()))
print(json.dumps(first_team["events"][0], ensure_ascii=False, indent=2))

# 2. 두 팀의 최근 경기 날짜와 결과
print("\n===== 최근 경기 목록 =====")
for team in data["lastFiveGames"]:
    print("---", team["team"]["displayName"], "---")
    for game in team["events"]:
        print(game.get("gameDate"), game.get("gameResult"), game.get("atVs"), game.get("opponent", {}).get("displayName"))