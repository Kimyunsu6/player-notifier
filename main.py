import os
import json
import time
from datetime import datetime, timezone
import espn
import alerts
import kv

LIVE_INTERVAL = 30       # 경기 중 간격 (초)
WAIT_INTERVAL = 300      # 명단 기다릴 때 간격 (초)
LINEUP_MINUTES = 60      # 킥오프 몇 분 전부터 확인할지
MAX_RUN_MINUTES = 240    # 한 번 실행에서 최대 몇 분까지 돌지


# KV의 사용자 설정 + 선수 사전으로 감시 목록 만들기
def load_watch_list():
    # 선수 사전을 "ID -> 선수 정보" 딕셔너리로
    db = {}
    for p in kv.get_json("player_db") or []:
        db[p["id"]] = p

    guild_channels = {}     # 서버ID -> 알림 채널ID
    watch = {}              # 선수ID -> 감시 정보

    for key in kv.list_keys("user:"):
        user_id = key.replace("user:", "")
        user = kv.get_json(key)
        if user is None:
            continue

        # 이 사용자 서버의 알림 채널 (한 번만 읽기)
        gid = user.get("guild_id")
        if gid not in guild_channels:
            g = kv.get_json("guild:" + str(gid))
            if g is None:
                guild_channels[gid] = None
            else:
                guild_channels[gid] = g["channel_id"]

        sub = {"user_id": user_id, "options": user["options"], "channel_id": guild_channels[gid]}

        for p in user["players"]:
            pid = p["id"]
            if pid not in db:
                continue        # 4대 리그 밖으로 이적 → 알림 끝

            if pid not in watch:
                watch[pid] = {
                    "espn_id": pid,
                    "name": db[pid]["name"],
                    "team_id": db[pid]["team_id"],
                    "league": db[pid]["league"],
                    "subs": []
                }
            watch[pid]["subs"].append(sub)

    return list(watch.values())


# 테스트 모드: 2024 테스트 선수 + 나에게만 알림
def load_test_watch_list():
    with open("experiments/players_test.json", "r", encoding="utf-8") as f:
        players = json.load(f)

    sub = {
        "user_id": os.getenv("TEST_USER_ID"),
        "options": {"lineup": True, "goals": True, "result": True},
        "channel_id": os.getenv("DISCORD_CHANNEL_ID")
    }
    for p in players:
        p["subs"] = [sub]
    return players


def load_sent():
    if os.path.exists("sent.json"):
        with open("sent.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_sent(sent):
    with open("sent.json", "w", encoding="utf-8") as f:
        json.dump(sent, f, ensure_ascii=False, indent=2)


# 킥오프까지 남은 시간 (분)
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


def all_reports_sent(match, sent):
    for p in match["players"]:
        if match["event_id"] + "_" + p["espn_id"] + "_report" not in sent:
            return False
    return True


# 정렬 기준: 이벤트 시간
def get_minute(alert):
    return alert["minute"]


# 경기 하나 확인
def check_match(match, sent, use_file):
    data = espn.get_summary(match["league"], match["event_id"], use_file=use_file)
    events = espn.get_events(data)

    pending = []        # 경기 중 알림 모으기
    found = []          # 명단에 있는 선수들 (리포트용)

    for p in match["players"]:
        player = espn.find_player(data, p["espn_id"])
        if player is None:
            print(" ", p["name"], "- 명단 아직 없음 또는 명단 제외")
            continue

        info = espn.get_match_info(data, player["team_id"])
        key_base = match["event_id"] + "_" + p["espn_id"]
        found.append([key_base, p, player, info])

        # 1. 명단 알림
        alerts.send_lineup(key_base, player, info, p["subs"], sent)

        # 2. 경기 중 이벤트 모으기
        if match["state"] == "in" or match["state"] == "post":
            pending = pending + alerts.collect_events(key_base, p["espn_id"], player, info, events, p["subs"])

    # 모든 선수 이벤트를 시간순으로 보내기
    pending.sort(key=get_minute)
    for a in pending:
        if alerts.already_sent(sent, a["key"]):
            continue
        alerts.send_to_subs(a["player"], a["league_name"], a["title"], a["description"], [], a["subs"], "goals")

    # 3. 경기 후 리포트
    if match["state"] == "post":
        for item in found:
            key_base = item[0]
            p = item[1]
            alerts.send_report(key_base, p["espn_id"], item[2], item[3], events, p["subs"], sent)


# 한 바퀴 확인: "live"(빠르게), "wait"(천천히), "none"(종료)
def run_once(players, sent, date, use_file):
    now = datetime.now(timezone.utc)
    matches = find_matches(players, date)
    result = "none"

    for m in matches:
        mins = minutes_until(m["date"], now)
        print("-", m["name"], "/ 상태:", m["state"], "/ 킥오프까지:", round(mins), "분")

        if m["state"] == "pre" and mins > LINEUP_MINUTES:
            continue
        if m["state"] == "post" and all_reports_sent(m, sent):
            continue

        check_match(m, sent, use_file)

        if m["state"] == "in" or (m["state"] == "pre" and mins <= 5):
            result = "live"
        elif m["state"] == "pre" and result != "live":
            result = "wait"

    return result


# ===== 실행 시작 =====
if __name__ == "__main__":
    TEST_MODE = False

    if TEST_MODE:
        players = load_test_watch_list()
        date = "20241201"
    else:
        players = load_watch_list()
        date = datetime.now(timezone.utc).strftime("%Y%m%d")

    print("감시 선수:", len(players), "명")
    sent = load_sent()
    start_time = time.time()

    while True:
        print("===== 확인", datetime.now().strftime("%H:%M:%S"), "=====")
        result = run_once(players, sent, date, TEST_MODE)
        save_sent(sent)

        if result == "none":
            print("지켜볼 경기 없음 - 종료")
            break

        if (time.time() - start_time) / 60 > MAX_RUN_MINUTES:
            print("최대 실행 시간 초과 - 종료")
            break

        if result == "live":
            time.sleep(LIVE_INTERVAL)
        else:
            time.sleep(WAIT_INTERVAL)

    print("보낸 알림 기록:", len(sent), "개")