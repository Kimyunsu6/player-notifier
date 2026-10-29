import json

EVENT_ID = 704401
file_name = "sample_espn_" + str(EVENT_ID) + ".json"

with open(file_name, "r", encoding="utf-8") as f:
    data = json.load(f)

# 교체 이벤트 1개, 골 이벤트 1개만 통째로 출력
printed_sub = False
printed_goal = False

for ke in data["keyEvents"]:
    event_type = ke.get("type", {}).get("text", "")

    if "Substitution" in event_type and not printed_sub:
        print("===== 교체 이벤트 =====")
        print(json.dumps(ke, ensure_ascii=False, indent=2))
        printed_sub = True

    if "Goal" in event_type and not printed_goal:
        print("===== 골 이벤트 =====")
        print(json.dumps(ke, ensure_ascii=False, indent=2))
        printed_goal = True