import streamlit as st
import requests
import hmac
import hashlib
import time
import json
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

# Bitvavo API access from Streamlit Secrets
API_KEY = st.secrets["API_KEY"]
API_SECRET = st.secrets["API_SECRET"]
BASE_URL = "https://api.bitvavo.com/v2"

# API signing function
def sign_request(method, path, body=''):
    timestamp = str(int(time.time() * 1000))
    message = timestamp + method + '/v2' + path + body
    signature = hmac.new(
        API_SECRET.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    headers = {
        'Bitvavo-Access-Key': API_KEY,
        'Bitvavo-Access-Signature': signature,
        'Bitvavo-Access-Timestamp': timestamp,
        'Bitvavo-Access-Window': '10000',
        'Content-Type': 'application/json'
    }
    return headers

# Fetch trades
@st.cache_data(ttl=600)
def fetch_trades():
    r = requests.get(
        BASE_URL + "/trades?market=BTC-EUR&limit=500",
        headers=sign_request("GET", "/trades?market=BTC-EUR&limit=500")
    )
    return r.json()

# Fetch BTC balance
def get_balance():
    r = requests.get(BASE_URL + "/balance/BTC", headers=sign_request("GET", "/balance/BTC"))
    return float(r.json().get("available", 0))

# Fetch BTC price
@st.cache_data(ttl=60)
def get_current_price():
    r = requests.get(BASE_URL + "/tickerPrice?market=BTC-EUR")
    return float(r.json().get("price", 0))

# UI
st.title("📈 Mein Bitcoin Dashboard")

# Load data
trades = fetch_trades()
btc_balance = get_balance()
current_price = get_current_price()

# Filter nur Käufe
buy_trades = [t for t in trades if t['side'] == 'buy']

# In DataFrame laden
df = pd.DataFrame(buy_trades)
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df['amount'] = df['amount'].astype(float)
df['amountQuote'] = df['amountQuote'].astype(float)
df['fee'] = df['fee'].astype(float)

# Berechnungen
investiert = df['amountQuote'].sum()
bestand = df['amount'].sum()
dca = investiert / bestand if bestand else 0
wert = btc_balance * current_price
gewinn = wert - investiert
entwicklung = (gewinn / investiert) * 100 if investiert else 0

# Anzeige
st.metric("BTC Bestand", f"{btc_balance:.6f} BTC")
st.metric("Investierte Summe", f"{investiert:.2f} €")
st.metric("Aktueller Wert", f"{wert:.2f} €")
st.metric("DCA (Durchschnittspreis)", f"{dca:.2f} €/BTC")
st.metric("% Entwicklung", f"{entwicklung:.2f} %")

# Diagramm: Portfolioentwicklung (Kumulierte Investition)
df['cum_eur'] = df['amountQuote'].cumsum()
df['cum_btc'] = df['amount'].cumsum()
df['btc_wert'] = df['cum_btc'] * current_price

st.subheader("🌐 Portfolioentwicklung")
fig, ax = plt.subplots()
ax.plot(df['timestamp'], df['cum_eur'], label="Investiert (€)")
ax.plot(df['timestamp'], df['btc_wert'], label="Wert aktuell (€)")
ax.set_ylabel("€")
ax.set_xlabel("Datum")
ax.legend()
st.pyplot(fig)

st.subheader("📊 Transaktionen")
st.dataframe(df[['timestamp', 'amount', 'amountQuote', 'fee']].sort_values('timestamp', ascending=False))
