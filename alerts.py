from discord_notify import send_embed


# 이미 보낸 알림이면 True, 처음이면 기록하고 False
def already_sent(sent, key):
    if key in sent:
        return True
    sent.append(key)
    return False


# ===== 1. 선발 / 벤치 알림 =====
def send_lineup(key_base, player, info, sent):
    if already_sent(sent, key_base + "_lineup"):
        return

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


# ===== 2. 경기 중 이벤트 알림 =====
def send_events(key_base, player_id, player, info, events, sent):
    was_bench = (player["starter"] == False)
    my_score = 0
    opp_score = 0
    name = "**" + player["name"] + "**"

    for e in events:
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
            was_bench = False
            if not already_sent(sent, key_base + "_sub_" + e["minute_text"]):
                if ids[0] == player_id:
                    other = e["names"][1]
                else:
                    other = e["names"][0]
                send_embed(player, info["league_name"], "SUB ON  " + e["minute_text"], name + "\n" + other + " 대신 투입", [])

        # 골 / 도움
        if e["scoring"]:
            if ids[0] == player_id and "Own Goal" not in e["text"]:
                if not already_sent(sent, key_base + "_goal_" + e["minute_text"]):
                    send_embed(player, info["league_name"], "GOAL  " + e["minute_text"], name + "\n" + score_text, [])
            if len(ids) > 1 and ids[1] == player_id:
                if not already_sent(sent, key_base + "_assist_" + e["minute_text"]):
                    send_embed(player, info["league_name"], "ASSIST  " + e["minute_text"], name + "\n" + score_text, [])

        # 퇴장
        if "Red Card" in e["text"] and ids[0] == player_id:
            if not already_sent(sent, key_base + "_red_" + e["minute_text"]):
                send_embed(player, info["league_name"], "RED CARD  " + e["minute_text"], name, [])


# ===== 3. 경기 후 리포트 =====
def send_report(key_base, player_id, player, info, events, sent):
    if key_base + "_report" in sent:
        return

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

    sent.append(key_base + "_report")   # 미출전이어도 다시 확인하지 않게 기록

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