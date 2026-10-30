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