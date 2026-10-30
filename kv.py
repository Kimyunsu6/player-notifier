import os
import json
import requests
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()
ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
KV_ID = os.getenv("CLOUDFLARE_KV_ID")

BASE_URL = "https://api.cloudflare.com/client/v4/accounts/" + str(ACCOUNT_ID) + "/storage/kv/namespaces/" + str(KV_ID)
HEADERS = {"Authorization": "Bearer " + str(API_TOKEN)}


# 이름이 prefix로 시작하는 키 목록 (예: "user:")
def list_keys(prefix):
    url = BASE_URL + "/keys"
    response = requests.get(url, headers=HEADERS, params={"prefix": prefix})
    data = response.json()

    keys = []
    for item in data.get("result", []):
        keys.append(item["name"])
    return keys


# 키 하나의 값 읽기 (JSON으로). 없으면 None
def get_json(key):
    url = BASE_URL + "/values/" + quote(key, safe="")
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return None
    return json.loads(response.text)


# 키 하나에 값 저장 (JSON으로)
def put_json(key, value):
    url = BASE_URL + "/values/" + quote(key, safe="")
    response = requests.put(url, headers=HEADERS, data=json.dumps(value, ensure_ascii=False).encode("utf-8"))
    return response.status_code


# ===== 직접 실행했을 때만 하는 테스트 =====
if __name__ == "__main__":
    print("===== 사용자 =====")
    for key in list_keys("user:"):
        print(key, get_json(key))

    print("\n===== 서버 =====")
    for key in list_keys("guild:"):
        print(key, get_json(key))

    db = get_json("player_db")
    if db is None:
        print("\n선수 사전: 없음")
    else:
        print("\n선수 사전:", len(db), "명")