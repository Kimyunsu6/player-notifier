import json

PLAYER_ID = "149945"    # Tom Cairney (ESPN ID는 문자열!)
EVENT_ID = 704401
file_name = "sample_espn_" + str(EVENT_ID) + ".json"


# "62'" -> 62, "90'+5'" -> 95 로 바꾸는 함수
def to_minute(text):
    text = text.replace("'", "")        # 따옴표 제거
    if "+" in text:
        parts = text.split("+")         # "90+5" -> ["90", "5"]
        return int(parts[0]) + int(parts[1])
    return int(text)


with open(file_name, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- 0. (테스트용) 벤치 선수 ID 목록 보기 ----------
print("===== 벤치 선수 목록 =====")
for team in data["rosters"]:
    for p in team["roster"]:
        if p["starter"] == False:
            print(p["athlete"]["id"], p["athlete"]["displayName"])
print()

# ---------- 1. 선발 / 벤치 / 명단 제외 ----------
status = "명단 제외"
player_name = ""
team_name = ""

for team in data["rosters"]:
    for p in team["roster"]:
        if p["athlete"]["id"] == PLAYER_ID:
            player_name = p["athlete"]["displayName"]
            team_name = team["team"]["displayName"]
            if p["starter"] == True:
                status = "선발"
            else:
                status = "벤치"

print("선수:", player_name, "/", team_name)
print("명단:", status)

if status == "명단 제외":
    exit()

# ---------- 2. 이벤트 (교체, 골, 도움, 퇴장) ----------
was_bench = (status == "벤치")
in_minute = 0       # 들어간 시간 (선발이면 0분)
out_minute = 90     # 나간 시간 (안 나가면 90분)

for ke in data["keyEvents"]:
    event_type = ke["type"]["type"]
    event_text = ke["type"]["text"]
    minute_text = ke["clock"]["displayValue"]
    if minute_text == "":
        continue                        # 킥오프처럼 시간이 없는 이벤트는 건너뛰기
    minute_num = to_minute(minute_text)

    # 이벤트에 나온 선수 ID, 이름 목록
    ids = []
    names = []
    for part in ke.get("participants", []):
        ids.append(part["athlete"]["id"])
        names.append(part["athlete"]["displayName"])

    # 교체
    if event_type == "substitution" and PLAYER_ID in ids:
        # 상대 선수 = 목록에서 내가 아닌 쪽
        if ids[0] == PLAYER_ID:
            other = names[1]
        else:
            other = names[0]

        if was_bench:
            print(minute_text, "교체 투입 (", other, "대신 )")
            in_minute = minute_num
            was_bench = False
        else:
            print(minute_text, "교체 아웃 (", other, "투입 )")
            out_minute = minute_num

    # 골 / 도움 (득점 인정된 것만)
    if ke.get("scoringPlay") == True and len(ids) > 0:
        if ids[0] == PLAYER_ID and "Own Goal" not in event_text:
            print(minute_text, "골!")
        if len(ids) > 1 and ids[1] == PLAYER_ID:
            print(minute_text, "도움!")

    # 퇴장
    if "Red Card" in event_text and len(ids) > 0 and ids[0] == PLAYER_ID:
        print(minute_text, "퇴장")
        out_minute = minute_num

# ---------- 3. 출전 시간 계산 ----------
if status == "벤치" and in_minute == 0:
    print("출전 시간: 0분 (미출전)")
else:
    minutes = out_minute - in_minute
    print("출전 시간:", minutes, "분")