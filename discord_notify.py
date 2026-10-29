import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


# 임베드 하나 보내기
# player: espn.find_player()의 결과 (팀 이름, 로고, 색 사용)
def send_embed(player, league_name, title, description, fields):
    embed = {
        "author": {"name": player["team_name"]},
        "title": title,
        "description": description,
        "color": player["team_color"],
        "thumbnail": {"url": player["team_logo"]},
        "fields": fields,
        "footer": {"text": league_name}
    }
    response = requests.post(WEBHOOK_URL, json={"embeds": [embed]})
    print("전송:", title, "/ 응답 코드:", response.status_code)
    time.sleep(1)       # 너무 빨리 보내지 않기
    return response.status_code


# ===== 직접 실행했을 때만 하는 테스트 =====
if __name__ == "__main__":
    test_player = {
        "team_name": "Test FC",
        "team_logo": "https://a.espncdn.com/i/teamlogos/soccer/500/367.png",
        "team_color": 0x5865F2
    }
    send_embed(test_player, "Test League", "TEST", "**discord_notify.py** 연결 확인", [])