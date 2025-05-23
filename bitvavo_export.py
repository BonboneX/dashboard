import os
import json
import time
import hmac
import hashlib
import requests
from datetime import datetime, timedelta
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
    url = "/trades?market=BTC-EUR&limit=500"
    r = requests.get(API_URL + url, headers=sign_request("GET", url))
    print("🔄 Trades Antwort:", r.status_code, r.text)
    return r.json()


def get_balance():
    url = "/balance/BTC"
    r = requests.get(API_URL + url, headers=sign_request("GET", url))
    print("🔄 Balance Antwort:", r.status_code, r.text)
    try:
        return float(r.json().get("available", 0))
    except Exception as e:
        print("❌ Fehler beim Parsen von BTC-Balance:", str(e))
        return 0.0


def get_current_price():
    r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eur")
    print("🔄 BTC-Preis Antwort:", r.status_code, r.text)
    return float(r.json()["bitcoin"]["eur"])


def get_yesterday_closing_price():
    try:
        yesterday = datetime.utcnow() - timedelta(days=1)
        date_str_display = yesterday.strftime("%Y-%m-%d")
        date_str_query = yesterday.strftime("%d-%m-%Y")
        url = f"https://api.coingecko.com/api/v3/coins/bitcoin/history?date={date_str_query}&localization=false"
        r = requests.get(url)
        price = r.json()["market_data"]["current_price"]["eur"]
        return date_str_display, price
    except Exception as e:
        print("⚠️ Fehler beim Abrufen des Vortages-Preises:", e)
        return None, None


def save_to_github(data):
    url = f"https://api.github.com/repos/{REPO}/contents/{FILENAME}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

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
        print("❌ Fehler beim Pushen:", r.status_code, r.text)
    else:
        print("✅ Datei erfolgreich aktualisiert")


def main():
    trades = fetch_trades()
    price = get_current_price()
    btc_balance = get_balance()

    # Bestehende Daten laden
    url = f"https://raw.githubusercontent.com/{REPO}/main/{FILENAME}"
    try:
        existing = requests.get(url).json()
    except:
        existing = {}

    # Daily Prices initialisieren & fixen Preis setzen
    if "daily_prices" not in existing:
        existing["daily_prices"] = {}
    existing["daily_prices"]["2025-05-22"] = 98308.00

    # Closing Price für gestern hinzufügen
    yday_key, yday_price = get_yesterday_closing_price()
    if yday_key and yday_price:
        existing["daily_prices"][yday_key] = yday_price

    # Neue Daten eintragen
    existing["timestamp"] = datetime.utcnow().isoformat()
    existing["btc_balance"] = btc_balance
    existing["btc_price_eur"] = price
    existing["trades"] = trades

    json_data = json.dumps(existing, indent=2)
    save_to_github(json_data)


if __name__ == "__main__":
    main()
