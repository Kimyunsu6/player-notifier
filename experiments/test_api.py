import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_FOOTBALL_KEY")

url = "https://v3.football.api-sports.io/status"
headers = {
    "x-apisports-key": api_key
}

response = requests.get(url, headers=headers)
data = response.json()

print("응답 코드:", response.status_code)
print("플랜:", data["response"]["subscription"]["plan"])
print("오늘 사용량:", data["response"]["requests"]["current"])
print("하루 한도:", data["response"]["requests"]["limit_day"])