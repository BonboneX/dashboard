import os
import json
import time
import hmac
import hashlib
import requests
from datetime import datetime
import base64

# Konfiguration
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "BonboneX/dashboard"
FILENAME = "btc_data.json"
API_URL = "https://api.bitvavo.com/v2"

def sign_request(method, path, body=''):
    timestamp = str(int(time.time() * 1000))
    message = timestamp + method + '/v2' + path + body
    signature = hmac.new(API_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()
    return {
        'Bitvavo-Access-Key': API_KEY,
        'Bitvavo-Access-Signature': signature,
        'Bitvavo-Access-Timestamp': timestamp,
        'Bitvavo-Access-Window': '10000',
        'Content-Type': 'application/json'
    }

def fetch_trades():
    r = requests.get(API_URL + "/trades?market=BTC-EUR&limit=500", headers=sign_request("GET", "/trades?market=BTC-EUR&limit=500"))
    return r.json()

def get_balance():
    r = requests.get(API_URL + "/balance/BTC", headers=sign_request("GET", "/balance/BTC"))
    return float(r.json().get("available", 0))

def get_current_price():
    r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eur")
    return float(r.json()["bitcoin"]["eur"])

def save_to_github(data):
    url = f"https://api.github.com/repos/{REPO}/contents/{FILENAME}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Bestehenden File-SHA holen
    get = requests.get(url, headers=headers)
    sha = get.json().get("sha", None)

    payload = {
        "message": f"Update {FILENAME}",
        "content": base64.b64encode(data.encode()).decode(),
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha

    r = requests.put(url, headers=headers, data=json.dumps(payload))
    if r.status_code not in [200, 201]:
        print("Fehler beim Pushen:", r.status_code, r.text)
    else:
        print("✅ Datei erfolgreich aktualisiert")

def main():
    trades = fetch_trades()
    price = get_current_price()
    btc_balance = get_balance()

    data = {
        "timestamp": datetime.utcnow().isoformat(),
        "btc_balance": btc_balance,
        "btc_price_eur": price,
        "trades": trades
    }

    json_data = json.dumps(data, indent=2)
    save_to_github(json_data)

if __name__ == "__main__":
    main()