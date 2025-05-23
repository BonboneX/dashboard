
import streamlit as st
import pandas as pd
from datetime import datetime
import altair as alt

st.set_page_config(page_title="📈 Mein Bitcoin Dashboard", layout="wide")

st.title("📈 Mein Bitcoin Dashboard")
st.success("Daten erfolgreich geladen")

# Daten vorbereiten
data = {
    "date_str": ["2025-05-22", "2025-05-23"],
    "cumulative_btc": [0.000204, 0.000408],
    "closing_price": [97709, 95471],
    "portfolio_value": [19.949247, 38.909206],
}
df = pd.DataFrame(data)
df["date"] = pd.to_datetime(df["date_str"])

# Statistiken berechnen
latest_value = df["portfolio_value"].iloc[-1]
invested = 20 * len(df)
performance = ((latest_value - invested) / invested) * 100

# Spaltenanzeige
col1, col2, col3, col4 = st.columns(4)
col1.metric("🔥 Aktueller BTC-Wert", f"{latest_value:.2f} €")
col2.metric("💰 Investiertes Kapital", f"{invested:.2f} €")
col3.metric("📊 Performance", f"{performance:.2f} %")

# Diagramm
st.markdown("📉 **BTC-Wertentwicklung (Portfolio gesamtwert)**")
chart = alt.Chart(df).mark_line(point=True).encode(
    x=alt.X("date:T", title="Datum"),
    y=alt.Y("portfolio_value:Q", title="Portfoliowert (€)"),
    tooltip=["date_str", "portfolio_value"]
).properties(width=1000, height=400)
st.altair_chart(chart, use_container_width=True)
