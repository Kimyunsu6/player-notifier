import requests
import espn

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/"

league = input("리그 코드 (예: ita.1): ").strip()
date = input("UTC 날짜 (예: 20261029): ").strip()
event_id = input("경기 ID: ").strip()

board = espn.get_scoreboard(league, date)

for event in board["events"]:
    if event["id"] == event_id:
        for c in event["competitions"][0]["competitors"]:
            team = c["team"]
            print()
            print("=====", team["displayName"], "/ team_id:", team["id"], "=====")

            roster = requests.get(BASE_URL + league + "/teams/" + team["id"] + "/roster").json()
            for a in roster.get("athletes", []):
                jersey = a.get("jersey", "-")
                position = a.get("position", {}).get("abbreviation", "-")
                print(a["id"], "| 등번호", jersey, "|", position, "|", a["displayName"])