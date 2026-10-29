import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_FOOTBALL_KEY")

url = "https://v3.football.api-sports.io/fixtures"
headers = {
    "x-apisports-key": api_key
}

params = {
    "league": 39,
    "season": 2024,
    "from": "2024-12-01",
    "to": "2024-12-07",
    "timezone": "Asia/Seoul"
}

response = requests.get(url, headers=headers, params=params)
data = response.json()

print("에러:", data["errors"])
print("경기 수:", data["results"])
print("-----")

for match in data["response"]:
    date = match["fixture"]["date"]
    home = match["teams"]["home"]["name"]
    away = match["teams"]["away"]["name"]
    print(match["fixture"]["id"], date[:16], home, "vs", away)