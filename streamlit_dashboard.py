import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
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

@st.cache_data(ttl=3600)
def get_yesterday_closing_price():
    try:
        yesterday = datetime.today() - timedelta(days=1)
        date_str = yesterday.strftime("%d-%m-%Y")
        url = f"https://api.coingecko.com/api/v3/coins/bitcoin/history?date={date_str}&localization=false"
        r = requests.get(url)
        return date_str, r.json()["market_data"]["current_price"]["eur"]
    except:
        return None, None

data = load_data()
current_btc_price = get_current_btc_price()
yesterday_str, closing_price = get_yesterday_closing_price()

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

    # BTC Bestand kumuliert
    buys["cumulative_btc"] = buys["amount"].cumsum()

    # Closing-Preise oder Fallback mit aktuellem Preis
    prices = data.get("daily_prices", {})
    buys["date_str"] = buys["date"].astype(str)
    buys["closing_price"] = buys["date_str"].map(prices)

    # Aktuellen Preis für letzte Zeile einsetzen, wenn kein Preis verfügbar
    if current_btc_price and buys["closing_price"].isna().any():
        latest_date = buys["date_str"].max()
        buys.loc[buys["date_str"] == latest_date, "closing_price"] = current_btc_price

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
    chart = alt.Chart(buys.dropna(subset=["portfolio_value"])).mark_line(point=True).encode(
        x=alt.X("date:T", title="Datum"),
        y=alt.Y("portfolio_value:Q", title="Portfoliowert (€)"),
        tooltip=["date_str", "portfolio_value"]
    ).properties(width=1000, height=400)
    st.altair_chart(chart, use_container_width=True)

    # Transaktionen
    st.markdown("#### 📜 Transaktionen")
    st.dataframe(buys[["timestamp", "amount", "price", "fee"]].sort_values("timestamp", ascending=False), use_container_width=True)
else:
    st.warning("⚠️ Keine Daten gefunden oder Fehler beim Laden.")
