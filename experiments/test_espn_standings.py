import json

EVENT_ID = 704401
file_name = "sample_espn_" + str(EVENT_ID) + ".json"

with open(file_name, "r", encoding="utf-8") as f:
    data = json.load(f)

standings = data["standings"]

# 1. standings 안에 어떤 항목이 있는지
print("===== standings 항목 이름 =====")
print(list(standings.keys()))

# 2. 첫 번째 그룹 안의 항목 이름
group = standings["groups"][0]
print("\n===== groups[0] 항목 이름 =====")
print(list(group.keys()))

# 3. 순위표 첫 번째 팀 하나를 통째로
print("\n===== 첫 번째 팀 =====")
first = group["standings"]["entries"][0]
print(json.dumps(first, ensure_ascii=False, indent=2))