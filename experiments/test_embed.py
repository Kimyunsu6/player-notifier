import os
import requests
from dotenv import load_dotenv

load_dotenv()
webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

# 카드(임베드) 내용
embed = {
    "title": "⚽ 선발 출전!",
    "description": "**테스트 선수**가 오늘 경기에 선발로 나옵니다.",
    "color": 0x1E90FF,  # 색깔 (16진수 색상 코드)
    "thumbnail": {
        "url": "https://media.api-sports.io/football/teams/47.png"
    },
    "fields": [
        {"name": "상대팀", "value": "테스트 FC", "inline": True},
        {"name": "킥오프", "value": "오늘 23:30", "inline": True},
        {"name": "승리 확률", "value": "45%", "inline": True},
        {"name": "리그 순위", "value": "4위 vs 12위", "inline": False}
    ],
    "footer": {
        "text": "프리미어리그 · 출전 알리미"
    }
}

data = {
    "embeds": [embed]
}

response = requests.post(webhook_url, json=data)
print("응답 코드:", response.status_code)