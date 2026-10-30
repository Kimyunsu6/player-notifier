from discord_notify import send_embed


# 이미 보낸 알림이면 True, 처음이면 기록하고 False
def already_sent(sent, key):
    if key in sent:
        return True
    sent.append(key)
    return False


# 구독자 중 option을 켠 사람만 골라서, 채널별로 멘션해서 보내기
# option: "lineup", "goals", "result"
def send_to_subs(player, league_name, title, description, fields, subs, option):
    channels = {}       # 채널ID -> [사용자ID, ...]
    for s in subs:
        if s["options"].get(option, False) == False:
            continue
        ch = s["channel_id"]
        if ch is None:
            continue
        if ch not in channels:
            channels[ch] = []
        channels[ch].append(s["user_id"])

    if len(channels) == 0:
        print("  (아무도 이 알림을 켜지 않음:", title, ")")
        return

    for ch in channels:
        send_embed(player, league_name, title, description, fields, channels[ch], ch)


# ===== 1. 선발 / 벤치 알림 =====
def send_lineup(key_base, player, info, subs, sent):
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
    send_to_subs(player, info["league_name"], title, description, fields, subs, "lineup")


# ===== 2. 경기 중 이벤트 모으기 (보내지는 않음 → main에서 시간순 정렬 후 보냄) =====
def collect_events(key_base, player_id, player, info, events, subs):
    result = []
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
            if ids[0] == player_id:
                other = e["names"][1]
            else:
                other = e["names"][0]
            result.append({
                "key": key_base + "_sub_" + e["minute_text"],
                "minute": e["minute"],
                "title": "SUB ON  " + e["minute_text"],
                "description": name + "\n" + other + " 대신 투입"
            })

        # 골 / 도움
        if e["scoring"]:
            if ids[0] == player_id and "Own Goal" not in e["text"]:
                result.append({
                    "key": key_base + "_goal_" + e["minute_text"],
                    "minute": e["minute"],
                    "title": "GOAL  " + e["minute_text"],
                    "description": name + "\n" + score_text
                })
            if len(ids) > 1 and ids[1] == player_id:
                result.append({
                    "key": key_base + "_assist_" + e["minute_text"],
                    "minute": e["minute"],
                    "title": "ASSIST  " + e["minute_text"],
                    "description": name + "\n" + score_text
                })

        # 퇴장
        if "Red Card" in e["text"] and ids[0] == player_id:
            result.append({
                "key": key_base + "_red_" + e["minute_text"],
                "minute": e["minute"],
                "title": "RED CARD  " + e["minute_text"],
                "description": name
            })

    # 보낼 때 필요한 정보 같이 담기
    for a in result:
        a["player"] = player
        a["league_name"] = info["league_name"]
        a["subs"] = subs

    return result


# ===== 3. 경기 후 리포트 =====
def send_report(key_base, player_id, player, info, events, subs, sent):
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

    sent.append(key_base + "_report")

    if played == False:
        print(" ", player["name"], "- 미출전, 리포트 없음")
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
    send_to_subs(player, info["league_name"], "FULL TIME", description, fields, subs, "result")