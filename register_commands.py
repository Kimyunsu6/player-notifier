import os
import requests
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
APP_ID = os.getenv("DISCORD_APP_ID")

# 등록할 명령어 목록
commands = [
    {
        "name": "핑",
        "description": "봇이 살아있는지 확인",
        "type": 1
    },
    {
        "name": "선수추가",
        "description": "알림 받을 선수 추가",
        "type": 1,
        "options": [
            {
                "type": 3,
                "name": "선수",
                "description": "선수 이름 (영어 2글자 이상 입력)",
                "required": True,
                "autocomplete": True
            }
        ]
    },
    {
        "name": "선수삭제",
        "description": "알림 받던 선수 삭제",
        "type": 1,
        "options": [
            {
                "type": 3,
                "name": "선수",
                "description": "삭제할 선수",
                "required": True,
                "autocomplete": True
            }
        ]
    },
    {
        "name": "내선수",
        "description": "내가 등록한 선수와 알림 옵션 보기",
        "type": 1
    }
]

url = "https://discord.com/api/v10/applications/" + APP_ID + "/commands"
headers = {"Authorization": "Bot " + BOT_TOKEN}

# PUT = 기존 명령어 목록을 이 목록으로 통째로 교체
response = requests.put(url, headers=headers, json=commands)

print("응답 코드:", response.status_code)
if response.status_code != 200:
    print("에러 내용:", response.text)
else:
    for c in response.json():
        print("등록됨: /" + c["name"])