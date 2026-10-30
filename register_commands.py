import os
import requests
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
APP_ID = os.getenv("DISCORD_APP_ID")

# 켜기/끄기 보기 (여러 번 쓰니까 변수로)
ON_OFF = [
    {"name": "켜기", "value": "on"},
    {"name": "끄기", "value": "off"}
]

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
            {"type": 3, "name": "선수", "description": "선수 이름 (영어 2글자 이상 입력)", "required": True, "autocomplete": True}
        ]
    },
    {
        "name": "선수삭제",
        "description": "알림 받던 선수 삭제",
        "type": 1,
        "options": [
            {"type": 3, "name": "선수", "description": "삭제할 선수", "required": True, "autocomplete": True}
        ]
    },
    {
        "name": "내선수",
        "description": "내가 등록한 선수와 알림 옵션 보기",
        "type": 1
    },
    {
        "name": "알림설정",
        "description": "받을 알림 종류 켜기/끄기 (옵션 없이 쓰면 현재 설정 보기)",
        "type": 1,
        "options": [
            {"type": 3, "name": "선발벤치", "description": "선발/벤치 명단 알림", "required": False, "choices": ON_OFF},
            {"type": 3, "name": "골어시", "description": "교체 투입, 골, 도움, 퇴장 알림", "required": False, "choices": ON_OFF},
            {"type": 3, "name": "결과", "description": "경기 후 리포트", "required": False, "choices": ON_OFF}
        ]
    },
    {
        "name": "알림채널",
        "description": "이 채널을 알림 채널로 지정 (서버 관리자용)",
        "type": 1,
        "default_member_permissions": "32"
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