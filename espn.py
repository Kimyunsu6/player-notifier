import os
import json
import requests
from datetime import datetime, timedelta

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/"


# ===== 1. ESPN에서 데이터 받기 =====

# 그날 경기 목록 (date 예: "20241201")
def get_scoreboard(league, date):
    url = BASE_URL + league + "/scoreboard"
    response = requests.get(url, params={"dates": date})
    return response.json()


# 경기 상세 (use_file=True면 저장된 파일 사용 - 테스트용)
def get_summary(league, event_id, use_file=False):
    file_name = "sample_espn_" + str(event_id) + ".json"

    if use_file and os.path.exists(file_name):
        with open(file_name, "r", encoding="utf-8") as f:
            return json.load(f)

    url = BASE_URL + league + "/summary"
    response = requests.get(url, params={"event": event_id})
    data = response.json()

    if use_file:
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return data


# ===== 2. 작은 도우미 함수 =====

# "62'" -> 62, "90'+5'" -> 95
def to_minute(text):
    text = text.replace("'", "")
    if "+" in text:
        parts = text.split("+")
        return int(parts[0]) + int(parts[1])
    return int(text)


# "WDL" -> "승무패"
def form_ko(text):
    text = text.replace("W", "승")
    text = text.replace("D", "무")
    text = text.replace("L", "패")
    return text


# 최근 5경기 결과 (과거 -> 최근)
def last_five(data, team_id):
    result = ""
    for t in data.get("lastFiveGames", []):
        if t["team"]["id"] == team_id:
            for game in t["events"]:
                result = result + game["gameResult"]
    return form_ko(result)


# 리그 순위
def get_rank(data, team_id):
    groups = data.get("standings", {}).get("groups", [])
    if len(groups) == 0:
        return "-"
    for entry in groups[0]["standings"]["entries"]:
        if entry["id"] == team_id:
            for s in entry["stats"]:
                if s["name"] == "rank":
                    return s["displayValue"] + "위"
    return "-"


# ===== 3. 데이터에서 필요한 정보 꺼내기 =====

# 명단에서 선수 찾기 (없으면 None)
def find_player(data, player_id):
    for team in data.get("rosters", []):
        for p in team.get("roster", []):
            if p["athlete"]["id"] == player_id:
                stats = {}
                for s in p.get("stats", []):
                    stats[s["name"]] = int(s["value"])

                color_text = team["team"].get("alternateColor", "5865F2")

                return {
                    "name": p["athlete"]["displayName"],
                    "starter": p["starter"],
                    "team_id": team["team"]["id"],
                    "team_name": team["team"]["displayName"],
                    "team_logo": team["team"]["logos"][0]["href"],
                    "team_color": int(color_text, 16),
                    "stats": stats
                }
    return None


# 경기 정보 (내 팀 기준)
def get_match_info(data, team_id):
    competition = data["header"]["competitions"][0]

    for c in competition["competitors"]:
        if c["team"]["id"] == team_id:
            my = c
        else:
            opp = c
        if c["homeAway"] == "home":
            home = c
        else:
            away = c

    # 킥오프: UTC -> 한국 시간
    utc_time = datetime.strptime(competition["date"], "%Y-%m-%dT%H:%MZ")
    kst_time = utc_time + timedelta(hours=9)

    # 시즌 성적 "5-4-4" -> "5승 4무 4패 · 19점"
    record = "-"
    if len(my.get("record", [])) >= 2:
        wdl = my["record"][0]["summary"].split("-")
        record = wdl[0] + "승 " + wdl[1] + "무 " + wdl[2] + "패 · " + my["record"][1]["summary"] + "점"

    my_abbr = my["team"]["abbreviation"]
    opp_abbr = opp["team"]["abbreviation"]

    if my["homeAway"] == "home":
        home_away = "홈"
    else:
        home_away = "원정"

    return {
        "opponent": opp["team"]["displayName"],
        "my_abbr": my_abbr,
        "opp_abbr": opp_abbr,
        "opp_id": opp["team"]["id"],
        "home_away": home_away,
        "kickoff": kst_time.strftime("%m.%d %H:%M"),
        "record": record,
        "my_form": my_abbr + "  " + last_five(data, team_id),
        "opp_form": opp_abbr + "  " + last_five(data, opp["team"]["id"]),
        "rank_text": my_abbr + " " + get_rank(data, team_id) + "  ·  " + opp_abbr + " " + get_rank(data, opp["team"]["id"]),
        "league_name": my["team"].get("groups", {}).get("name", ""),
        "final_score": home["team"]["displayName"] + " " + home.get("score", "0") + "-" + away.get("score", "0") + " " + away["team"]["displayName"]
    }


# 이벤트 목록을 쓰기 쉬운 모양으로 정리
def get_events(data):
    events = []
    for ke in data.get("keyEvents", []):
        minute_text = ke.get("clock", {}).get("displayValue", "")
        if minute_text == "":
            continue

        ids = []
        names = []
        for part in ke.get("participants", []):
            ids.append(part["athlete"]["id"])
            names.append(part["athlete"]["displayName"])

        events.append({
            "type": ke["type"]["type"],          # substitution 등
            "text": ke["type"]["text"],          # Goal - Volley, Red Card 등
            "minute_text": minute_text,          # 90'+5'
            "minute": to_minute(minute_text),    # 95
            "ids": ids,
            "names": names,
            "scoring": ke.get("scoringPlay") == True,
            "team_id": ke.get("team", {}).get("id", "")
        })
    return events


# ===== 이 파일을 직접 실행했을 때만 하는 테스트 =====
if __name__ == "__main__":
    data = get_summary("eng.1", 704401, use_file=True)

    player = find_player(data, "140033")
    print("선수:", player["name"], "/", player["team_name"], "/ 선발:", player["starter"])
    print("스탯:", player["stats"])

    info = get_match_info(data, player["team_id"])
    print("경기 정보:", info)

    print("이벤트 앞 3개:")
    events = get_events(data)
    for e in events[0:3]:
        print(" ", e)