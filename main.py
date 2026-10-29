import os
import json
import time
from datetime import datetime, timezone
import espn
import alerts

CHECK_INTERVAL = 60      # 반복 간격 (초)
LINEUP_MINUTES = 40      # 킥오프 몇 분 전부터 확인할지
MAX_RUN_MINUTES = 180    # 한 번 실행에서 최대 몇 분까지 돌지


# players.json 읽기
def load_players():
    with open("players.json", "r", encoding="utf-8") as f:
        return json.load(f)


# 보낸 알림 기록 읽기
def load_sent():
    if os.path.exists("sent.json"):
        with open("sent.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []


# 보낸 알림 기록 저장
def save_sent(sent):
    with open("sent.json", "w", encoding="utf-8") as f:
        json.dump(sent, f, ensure_ascii=False, indent=2)


# 킥오프까지 남은 시간 (분). 지났으면 음수
def minutes_until(date_text, now):
    kickoff = datetime.strptime(date_text, "%Y-%m-%dT%H:%MZ")
    kickoff = kickoff.replace(tzinfo=timezone.utc)
    return (kickoff - now).total_seconds() / 60


# 오늘 내 선수들이 뛰는 경기 찾기
def find_matches(players, date):
    leagues = []
    for p in players:
        if p["league"] not in leagues:
            leagues.append(p["league"])

    matches = []
    for league in leagues:
        board = espn.get_scoreboard(league, date)

        for event in board.get("events", []):
            team_ids = []
            for c in event["competitions"][0]["competitors"]:
                team_ids.append(c["team"]["id"])

            my_players = []
            for p in players:
                if p["league"] == league and p["team_id"] in team_ids:
                    my_players.append(p)

            if len(my_players) > 0:
                matches.append({
                    "event_id": event["id"],
                    "league": league,
                    "name": event["name"],
                    "date": event["date"],
                    "state": event["status"]["type"]["state"],
                    "players": my_players
                })

    return matches


# 이 경기의 리포트를 모든 선수에게 이미 보냈는지
def all_reports_sent(match, sent):
    for p in match["players"]:
        if match["event_id"] + "_" + p["espn_id"] + "_report" not in sent:
            return False
    return True


# 경기 하나 확인
def check_match(match, sent, use_file):
    data = espn.get_summary(match["league"], match["event_id"], use_file=use_file)
    events = espn.get_events(data)

    for p in match["players"]:
        player = espn.find_player(data, p["espn_id"])
        if player is None:
            print(" ", p["name"], "- 명단 아직 없음 또는 명단 제외")
            continue

        info = espn.get_match_info(data, player["team_id"])
        key_base = match["event_id"] + "_" + p["espn_id"]

        alerts.send_lineup(key_base, player, info, sent)

        if match["state"] == "in" or match["state"] == "post":
            alerts.send_events(key_base, p["espn_id"], player, info, events, sent)

        if match["state"] == "post":
            alerts.send_report(key_base, p["espn_id"], player, info, events, sent)


# 한 바퀴 확인. 계속 지켜볼 경기가 있으면 True
def run_once(players, sent, date, use_file):
    now = datetime.now(timezone.utc)
    matches = find_matches(players, date)
    keep_watching = False

    for m in matches:
        mins = minutes_until(m["date"], now)
        print("-", m["name"], "/ 상태:", m["state"], "/ 킥오프까지:", round(mins), "분")

        if m["state"] == "pre" and mins > LINEUP_MINUTES:
            continue                        # 아직 이름

        if m["state"] == "post" and all_reports_sent(m, sent):
            continue                        # 이미 다 끝난 경기

        check_match(m, sent, use_file)

        if m["state"] == "pre" or m["state"] == "in":
            keep_watching = True            # 곧 시작 or 진행 중

    return keep_watching


# ===== 실행 시작 =====
if __name__ == "__main__":
    TEST_MODE = True

    players = load_players()
    sent = load_sent()

    if TEST_MODE:
        date = "20241201"
    else:
        date = datetime.now(timezone.utc).strftime("%Y%m%d")

    start_time = time.time()

    while True:
        print("===== 확인", datetime.now().strftime("%H:%M:%S"), "=====")
        keep_watching = run_once(players, sent, date, TEST_MODE)
        save_sent(sent)

        if keep_watching == False:
            print("지켜볼 경기 없음 - 종료")
            break

        run_minutes = (time.time() - start_time) / 60
        if run_minutes > MAX_RUN_MINUTES:
            print("최대 실행 시간 초과 - 종료")
            break

        time.sleep(CHECK_INTERVAL)

    print("보낸 알림 기록:", len(sent), "개")