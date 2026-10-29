import requests

url = "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard"
params = {"dates": "20241201"}

response = requests.get(url, params=params)
print("응답 코드:", response.status_code)

data = response.json()

for event in data["events"]:
    print(event["id"], event["date"], event["name"])