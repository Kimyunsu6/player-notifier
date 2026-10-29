import os
import requests
from dotenv import load_dotenv

# .env 파일에서 웹훅 주소 읽기
load_dotenv()
webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

# 보낼 메시지
data = {
    "content": "출전 알리미 테스트 메시지입니다!"
}

# 디스코드로 전송
response = requests.post(webhook_url, json=data)

# 결과 확인
print("응답 코드:", response.status_code)