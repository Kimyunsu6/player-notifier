import json
import requests

EVENT_ID = 704401   # 토트넘 vs 풀럼 (ESPN)

url = "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/summary"
params = {"event": EVENT_ID}

response = requests.get(url, params=params)
print("응답 코드:", response.status_code)
data = response.json()

# 나중에 다시 보려고 파일로 저장 (.gitignore에 걸려서 GitHub엔 안 올라감)
with open("sample_espn_" + str(EVENT_ID) + ".json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# 1. 맨 위 항목 이름들
print("\n===== 최상위 항목 =====")
print(list(data.keys()))

# 2. 명단에서 손흥민 찾아서 통째로 출력
print("\n===== 손흥민 명단 정보 =====")
for team in data.get("rosters", []):
    for p in team.get("roster", []):
        if "Son" in p["athlete"]["displayName"]:
            print(json.dumps(p, ensure_ascii=False, indent=2))

# 3. 주요 이벤트 (골, 교체 등)
print("\n===== 주요 이벤트 =====")
for ke in data.get("keyEvents", []):
    event_type = ke.get("type", {}).get("text", "")
    minute = ke.get("clock", {}).get("displayValue", "")
    text = ke.get("text", "")
    print(minute, "|", event_type, "|", text)