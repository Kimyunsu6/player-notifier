import json

with open("players.json", "r", encoding="utf-8") as f:
    players = json.load(f)

print("등록된 선수:", len(players), "명")
for p in players:
    print("-", p["name"], "/ ESPN ID:", p["espn_id"], "/ 리그:", p["league"])