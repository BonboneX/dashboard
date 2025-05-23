import streamlit as st
import pandas as pd
import requests
import datetime

# GitHub-Rohdatei-URL (raw URL zur btc_data.json)
GITHUB_JSON_URL = "https://raw.githubusercontent.com/BonboneX/dashboard/main/btc_data.json"

st.set_page_config(page_title="📈 Bitcoin Dashboard", layout="wide")
st.title("📈 Mein Bitcoin Dashboard")

# Funktion: JSON laden
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

    # Käufe extrahieren
    trades["amount"] = trades["amount"].astype(float)
    trades["price"] = trades["price"].astype(float)
    trades["fee"] = trades["fee"].astype(float)
    trades["timestamp"] = pd.to_datetime(trades["timestamp"], unit="ms")

    buys = trades[trades["side"] == "buy"].copy()

    # DCA-Berechnung (durchschnittlicher Kaufpreis)
    total_invested_eur = (buys["amount"] * buys["price"]).sum()
    total_btc_bought = buys["amount"].sum()
    dca = total_invested_eur / total_btc_bought if total_btc_bought > 0 else 0

    current_value = btc_balance * btc_price
    total_fees = buys["fee"].sum()
    pnl_percent = ((current_value - total_invested_eur) / total_invested_eur * 100) if total_invested_eur > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Aktueller BTC-Bestand", f"{btc_balance:.8f} BTC")
    col2.metric("💶 Investiertes Kapital", f"{total_invested_eur:.2f} €")
    col3.metric("📊 Aktueller Wert", f"{current_value:.2f} €")
    col4.metric("📈 Performance", f"{pnl_percent:.2f} %")

    st.markdown("#### 🧮 Durchschnittlicher Kaufpreis (DCA)")
    st.code(f"{dca:.2f} € pro BTC", language="text")

    st.markdown("#### 📉 BTC-Wertentwicklung (visualisiert)")
    # Zeitreihe konstruieren (simuliert aus Transaktionsdaten)
    value_over_time = (buys[["timestamp", "amount", "price"]]
                       .assign(eur_value=lambda x: x["amount"] * x["price"])
                       .sort_values("timestamp"))

    value_over_time["cum_eur"] = value_over_time["eur_value"].cumsum()
    st.line_chart(value_over_time.set_index("timestamp")["cum_eur"])

    st.markdown("#### 📜 Transaktionen")
    st.dataframe(buys[["timestamp", "amount", "price", "fee"]].sort_values("timestamp", ascending=False), use_container_width=True)
else:
    st.warning("⚠️ Noch keine Daten gefunden.")