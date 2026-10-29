import requests

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/"
LEAGUES = {
    "eng.1": "프리미어리그",
    "esp.1": "라리가",
    "ita.1": "세리에A",
    "ger.1": "분데스리가"
}

# 1. 검색 조건 입력
keyword = input("선수 이름 (영어 일부, 예: son): ").strip().lower()
print("리그 선택: 1) 전체  2) eng.1  3) esp.1  4) ita.1  5) ger.1")
choice = input("번호: ").strip()

if choice == "2":
    search_leagues = ["eng.1"]
elif choice == "3":
    search_leagues = ["esp.1"]
elif choice == "4":
    search_leagues = ["ita.1"]
elif choice == "5":
    search_leagues = ["ger.1"]
else:
    search_leagues = ["eng.1", "esp.1", "ita.1", "ger.1"]

found = 0

# 2. 리그 -> 팀 -> 선수 명단 순서로 찾기
for league in search_leagues:
    print("검색 중:", LEAGUES[league], "...")
    teams_data = requests.get(BASE_URL + league + "/teams").json()
    teams = teams_data["sports"][0]["leagues"][0]["teams"]

    for t in teams:
        team = t["team"]
        roster = requests.get(BASE_URL + league + "/teams/" + team["id"] + "/roster").json()

        for athlete in roster.get("athletes", []):
            name = athlete.get("displayName", "")
            if keyword in name.lower():
                found = found + 1
                print()
                print("찾음:", name, "/", team["displayName"], "/", LEAGUES[league])
                print("players.json에 넣을 내용:")
                print('  {')
                print('    "name": "' + name + '",')
                print('    "espn_id": "' + athlete["id"] + '",')
                print('    "team_id": "' + team["id"] + '",')
                print('    "league": "' + league + '",')
                print('    "users": ["윤수"]')
                print('  }')

print()
print("검색 완료:", found, "명 찾음")