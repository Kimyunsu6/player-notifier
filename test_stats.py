import json

PLAYER_ID = 186         # 손흥민
FIXTURE_ID = 1208150
file_name = "sample_" + str(FIXTURE_ID) + ".json"

with open(file_name, "r", encoding="utf-8") as f:
    match = json.load(f)

# players: 팀별로 선수 기록이 들어 있음
for team in match["players"]:
    for p in team["players"]:
        if p["player"]["id"] == PLAYER_ID:
            print("선수:", p["player"]["name"])
            stats = p["statistics"][0]
            # 기록 전체를 보기 좋게 출력
            print(json.dumps(stats, ensure_ascii=False, indent=2))