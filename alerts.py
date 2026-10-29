import json
import espn
from discord_notify import send_embed


# ===== 1. 선발 / 벤치 알림 =====
def send_lineup(player, info):
    if player["starter"] == True:
        title = "STARTING XI"
    else:
        title = "ON THE BENCH"

    fields = [
        {"name": "킥오프", "value": info["kickoff"], "inline": True},
        {"name": "홈/원정", "value": info["home_away"], "inline": True},
        {"name": "시즌 성적", "value": info["record"], "inline": True},
        {"name": "리그 순위", "value": info["rank_text"], "inline": False},
        {"name": "최근 5경기 (과거 → 최근)", "value": info["my_form"] + "\n" + info["opp_form"], "inline": False}
    ]
    description = "**" + player["name"] + "**\nvs " + info["opponent"]
    send_embed(player, info["league_name"], title, description, fields)


# ===== 2. 경기 중 이벤트 알림 (교체 투입, 골, 도움, 퇴장) =====
def send_events(player_id, player, info, events):
    was_bench = (player["starter"] == False)
    my_score = 0
    opp_score = 0
    name = "**" + player["name"] + "**"

    for e in events:
        # 스코어는 모든 골에서 세기 (내 선수와 상관없어도)
        if e["scoring"]:
            if e["team_id"] == player["team_id"]:
                my_score = my_score + 1
            else:
                opp_score = opp_score + 1
        score_text = info["my_abbr"] + " " + str(my_score) + "-" + str(opp_score) + " " + info["opp_abbr"]

        ids = e["ids"]
        if player_id not in ids:
            continue

        # 교체 투입
        if e["type"] == "substitution" and was_bench:
            if ids[0] == player_id:
                other = e["names"][1]
            else:
                other = e["names"][0]
            send_embed(player, info["league_name"], "SUB ON  " + e["minute_text"], name + "\n" + other + " 대신 투입", [])
            was_bench = False

        # 골 / 도움
        if e["scoring"]:
            if ids[0] == player_id and "Own Goal" not in e["text"]:
                send_embed(player, info["league_name"], "GOAL  " + e["minute_text"], name + "\n" + score_text, [])
            if len(ids) > 1 and ids[1] == player_id:
                send_embed(player, info["league_name"], "ASSIST  " + e["minute_text"], name + "\n" + score_text, [])

        # 퇴장
        if "Red Card" in e["text"] and ids[0] == player_id:
            send_embed(player, info["league_name"], "RED CARD  " + e["minute_text"], name, [])


# ===== 3. 경기 후 리포트 =====
def send_report(player_id, player, info, events):
    was_bench = (player["starter"] == False)
    played = player["starter"]
    in_minute = 0
    out_minute = 90
    timeline = []

    for e in events:
        ids = e["ids"]
        if player_id not in ids:
            continue

        if e["type"] == "substitution":
            if was_bench:
                timeline.append(e["minute_text"] + " 투입")
                in_minute = e["minute"]
                was_bench = False
                played = True
            else:
                timeline.append(e["minute_text"] + " 교체 아웃")
                out_minute = e["minute"]

        if e["scoring"]:
            if ids[0] == player_id and "Own Goal" not in e["text"]:
                timeline.append(e["minute_text"] + " 골")
            if len(ids) > 1 and ids[1] == player_id:
                timeline.append(e["minute_text"] + " 도움")

        if "Yellow Card" in e["text"] and ids[0] == player_id:
            timeline.append(e["minute_text"] + " 경고")
        if "Red Card" in e["text"] and ids[0] == player_id:
            timeline.append(e["minute_text"] + " 퇴장")
            out_minute = e["minute"]

    if played == False:
        print(player["name"], "- 미출전, 리포트 없음")
        return

    if len(timeline) == 0:
        flow = "특이 사항 없음"
    else:
        flow = " → ".join(timeline)

    s = player["stats"]
    fields = [
        {"name": "출전 시간", "value": str(out_minute - in_minute) + "분", "inline": True},
        {"name": "골 / 도움", "value": str(s.get("totalGoals", 0)) + " / " + str(s.get("goalAssists", 0)), "inline": True},
        {"name": "슈팅 (유효)", "value": str(s.get("totalShots", 0)) + " (" + str(s.get("shotsOnTarget", 0)) + ")", "inline": True},
        {"name": "파울 유도", "value": str(s.get("foulsSuffered", 0)), "inline": True},
        {"name": "파울", "value": str(s.get("foulsCommitted", 0)), "inline": True},
        {"name": "경고 / 퇴장", "value": str(s.get("yellowCards", 0)) + " / " + str(s.get("redCards", 0)), "inline": True},
        {"name": "경기 흐름", "value": flow, "inline": False}
    ]
    description = "**" + player["name"] + "**\n" + info["final_score"]
    send_embed(player, info["league_name"], "FULL TIME", description, fields)


# ===== 직접 실행했을 때만: players.json의 모든 선수로 테스트 =====
if __name__ == "__main__":
    with open("players.json", "r", encoding="utf-8") as f:
        players = json.load(f)

    data = espn.get_summary("eng.1", 704401, use_file=True)
    events = espn.get_events(data)

    for p in players:
        player = espn.find_player(data, p["espn_id"])
        if player is None:
            print(p["name"], "- 이 경기 명단에 없음")
            continue

        info = espn.get_match_info(data, player["team_id"])
        print("=====", p["name"], "=====")
        send_lineup(player, info)
        send_events(p["espn_id"], player, info, events)
        send_report(p["espn_id"], player, info, events)