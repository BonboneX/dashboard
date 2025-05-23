import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import altair as alt
import json

st.set_page_config(page_title="📈 Mein Bitcoin Dashboard", layout="wide")
st.title("📈 Mein Bitcoin Dashboard")

# Datenquelle
GITHUB_JSON_URL = "https://raw.githubusercontent.com/BonboneX/dashboard/main/btc_data.json"

@st.cache_data(ttl=300)
def load_data():
    try:
        r = requests.get(GITHUB_JSON_URL)
        return r.json()
    except Exception as e:
        st.error(f"Fehler beim Laden der Daten: {e}")
        return None

@st.cache_data(ttl=300)
def get_current_btc_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eur")
        return r.json()["bitcoin"]["eur"]
    except:
        return None

data = load_data()
current_btc_price = get_current_btc_price()

if data:
    st.success("✅ Daten erfolgreich geladen")

    trades = pd.DataFrame(data["trades"])
    trades["timestamp"] = pd.to_datetime(trades["timestamp"], unit="ms")

    # Testdaten ausschließen
    test_timestamps = [
        "2025-05-22 21:48:46",
        "2025-05-22 21:45:09",
        "2025-05-22 18:40:26"
    ]
    trades = trades[~trades["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S").isin(test_timestamps)]

    # Nur Käufe
    buys = trades[trades["side"] == "buy"].copy()
    buys["amount"] = buys["amount"].astype(float)
    buys["price"] = buys["price"].astype(float)
    buys["fee"] = buys["fee"].astype(float)
    buys = buys.sort_values("timestamp")
    buys["date"] = buys["timestamp"].dt.date

    # BTC Bestand kumuliert & Closing-Preis von CoinGecko holen
    buys["cumulative_btc"] = buys["amount"].cumsum()

    # Closing Preise simuliert (z. B. von CoinGecko normalerweise)
    unique_dates = buys["date"].unique()
    prices = {}
    for d in unique_dates:
        prices[str(d)] = 95000 + hash(str(d)) % 3000  # Zufallswert als Platzhalter

    buys["closing_price"] = buys["date"].astype(str).map(prices)
    buys["portfolio_value"] = buys["cumulative_btc"] * buys["closing_price"]

    # Gesamtwerte
    total_btc = buys["cumulative_btc"].iloc[-1]
    invested = (buys["amount"] * buys["price"] + buys["fee"]).sum()
    dca = invested / total_btc if total_btc > 0 else 0
    live_value = total_btc * current_btc_price if current_btc_price else 0
    pnl = ((live_value - invested) / invested * 100) if invested > 0 else 0

    # Metriken anzeigen
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("💰 BTC-Bestand", f"{total_btc:.8f} BTC")
    col2.metric("💶 Investiert", f"{invested:.2f} €")
    col3.metric("🧮 DCA", f"{dca:.2f} €/BTC")
    col4.metric("📊 Aktueller Wert", f"{live_value:.2f} €")
    col5.metric("📈 Performance", f"{pnl:.2f} %")

    # Diagramm
    st.markdown("#### 📉 Portfolio-Wertentwicklung")
    chart = alt.Chart(buys).mark_line(point=True).encode(
        x=alt.X("date:T", title="Datum"),
        y=alt.Y("portfolio_value:Q", title="Portfoliowert (€)"),
        tooltip=["date:T", "portfolio_value"]
    ).properties(width=1000, height=400)
    st.altair_chart(chart, use_container_width=True)

    # Transaktionen
    st.markdown("#### 📜 Transaktionen")
    st.dataframe(buys[["timestamp", "amount", "price", "fee"]].sort_values("timestamp", ascending=False), use_container_width=True)
else:
    st.warning("⚠️ Keine Daten gefunden oder Fehler beim Laden.")
