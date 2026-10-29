import json
import requests

EVENT_ID = 704401
PLAYER_ID = "149945"    # 손흥민
file_name = "sample_espn_" + str(EVENT_ID) + ".json"

with open(file_name, "r", encoding="utf-8") as f:
    data = json.load(f)

# 1. rosters 안의 팀 정보
print("===== rosters 팀 정보 =====")
print(json.dumps(data["rosters"][0]["team"], ensure_ascii=False, indent=2))

# 2. header 안의 경기 팀 정보 (홈/원정, 점수 등)
print("\n===== header 팀 정보 =====")
competitor = data["header"]["competitions"][0]["competitors"][0]
print(json.dumps(competitor, ensure_ascii=False, indent=2))

# 3. 선수 사진 주소가 실제로 있는지 확인
photo_url = "https://a.espncdn.com/i/headshots/soccer/players/full/" + PLAYER_ID + ".png"
response = requests.get(photo_url)
print("\n===== 선수 사진 =====")
print(photo_url)
print("응답 코드:", response.status_code)