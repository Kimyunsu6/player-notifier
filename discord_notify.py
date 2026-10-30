import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DEFAULT_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
API_URL = "https://discord.com/api/v10"


# 임베드 하나 보내기
# player: espn.find_player()의 결과 (팀 이름, 로고, 색 사용)
# user_ids: 멘션할 디스코드 사용자 ID 목록 (없으면 멘션 안 함)
# channel_id: 보낼 채널 (없으면 .env의 기본 채널)
def send_embed(player, league_name, title, description, fields, user_ids=[], channel_id=None):
    if channel_id is None:
        channel_id = DEFAULT_CHANNEL_ID

    embed = {
        "author": {"name": player["team_name"]},
        "title": title,
        "description": description,
        "color": player["team_color"],
        "thumbnail": {"url": player["team_logo"]},
        "fields": fields,
        "footer": {"text": league_name}
    }

    mention_text = ""
    id_list = []
    for uid in user_ids:
        mention_text = mention_text + "<@" + str(uid) + "> "
        id_list.append(str(uid))

    body = {
        "content": mention_text,
        "embeds": [embed],
        "allowed_mentions": {"users": id_list}     # 이 사람들만 실제로 알림이 감
                }

    headers = {"Authorization": "Bot " + BOT_TOKEN}
    url = API_URL + "/channels/" + channel_id + "/messages"

    response = requests.post(url, headers=headers, json=body)
    print("전송:", title, "/ 응답 코드:", response.status_code)

    if response.status_code != 200:
        print("  에러 내용:", response.text)

    time.sleep(1)
    return response.status_code


# ===== 직접 실행했을 때만 하는 테스트 =====
if __name__ == "__main__":
    test_player = {
        "team_name": "Test FC",
        "team_logo": "https://a.espncdn.com/i/teamlogos/soccer/500/367.png",
        "team_color": 0x5865F2
    }
    MY_USER_ID = "여기에_내_사용자ID"     # 테스트용

    send_embed(test_player, "Test League", "BOT TEST", "봇으로 보낸 첫 메시지", [], ["345614195758465046"])