import sys
sys.path.append(".")
import espn
from datetime import datetime, timedelta

# 오늘 두 경기 (UTC 날짜 기준)
targets = [["eng.1", "Manchester United"], ["esp.1", "Levante"]]

for t in targets:
    board = espn.get_scoreboard(t[0], "20261031")
    for e in board["events"]:
        if t[1] in e["name"]:
            print("=====", e["name"], "=====")
            data = espn.get_summary(t[0], e["id"])
            for ke in data.get("keyEvents", []):
                clock = ke.get("clock", {}).get("displayValue", "")
                kind = ke["type"]["text"]
                wall = ke.get("wallclock", "")
                kst = ""
                if wall != "":
                    utc = datetime.strptime(wall[:19], "%Y-%m-%dT%H:%M:%S")
                    kst = (utc + timedelta(hours=9)).strftime("%H:%M:%S")
                print(kst, "|", clock, "|", kind)