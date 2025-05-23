import streamlit as st
import pandas as pd
import requests
import datetime

GITHUB_JSON_URL = "https://raw.githubusercontent.com/BonboneX/dashboard/main/btc_data.json"

st.set_page_config(page_title="📈 Bitcoin Dashboard", layout="wide")
st.title("📈 Mein Bitcoin Dashboard")

@st.cache_data(ttl=300)
def load_data():
    try:
        r = requests.get(GITHUB_JSON_URL)
        data = r.json()
        return data
    except Exception as e:
        st.error(f"Fehler beim Laden der Daten: {str(e)}")
        return None

data = load_data()

if data:
    st.success("✅ Daten erfolgreich geladen")

    btc_balance = float(data["btc_balance"])
    btc_price = float(data["btc_price_eur"])
    trades = pd.DataFrame(data["trades"])

    trades["amount"] = trades["amount"].astype(float)
    trades["price"] = trades["price"].astype(float)
    trades["fee"] = trades["fee"].astype(float)
    trades["timestamp"] = pd.to_datetime(trades["timestamp"], unit="ms")

    buys = trades[trades["side"] == "buy"].copy()
    buys["eur_value"] = buys["amount"] * buys["price"]

    # Korrekte Investitionsberechnung (inkl. Gebühren)
    total_invested_eur = buys["eur_value"].sum() + buys["fee"].sum()
    total_btc_bought = buys["amount"].sum()
    dca = total_invested_eur / total_btc_bought if total_btc_bought > 0 else 0

    current_value = btc_balance * btc_price
    pnl_percent = ((current_value - total_invested_eur) / total_invested_eur * 100) if total_invested_eur > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Aktueller BTC-Bestand", f"{btc_balance:.8f} BTC")
    col2.metric("💶 Investiertes Kapital", f"{total_invested_eur:.2f} €")
    col3.metric("📊 Aktueller Wert", f"{current_value:.2f} €")
    col4.metric("📈 Performance", f"{pnl_percent:.2f} %")

    st.markdown("#### 🧮 Durchschnittlicher Kaufpreis (DCA)")
    st.code(f"{dca:.2f} € pro BTC", language="text")

    st.markdown("#### 📉 BTC-Wertentwicklung (visualisiert)")
    buys["date"] = buys["timestamp"].dt.date
    daily = buys.groupby("date")["eur_value"].sum().cumsum().reset_index()
    daily.columns = ["Datum", "Investiert (EUR)"]
    st.line_chart(daily.set_index("Datum"))

    st.markdown("#### 📜 Transaktionen")
    st.dataframe(buys[["timestamp", "amount", "price", "fee"]].sort_values("timestamp", ascending=False), use_container_width=True)
else:
    st.warning("⚠️ Noch keine Daten gefunden.")