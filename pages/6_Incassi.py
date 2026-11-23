import streamlit as st
import pandas as pd
from datetime import date, timedelta

st.title("Incassi")

# Demo data
daily_revenue = [
    {"date": date.today() - timedelta(days=i), "revenue": round(100 + (i * 23.5), 2)}
    for i in range(7, 0, -1)
]
monthly_revenue = [
    {"month": "Gennaio 2025", "revenue": 2450.0},
    {"month": "Febbraio 2025", "revenue": 2890.0},
    {"month": "Marzo 2025", "revenue": 3120.0},
]

col1, col2 = st.columns(2)
with col1:
    st.subheader("Riepilogo giornaliero (ultimi 7 giorni)")
    df_daily = pd.DataFrame(daily_revenue)
    df_daily = df_daily.rename(columns={"date": "Data", "revenue": "Incasso"})
    st.dataframe(df_daily, hide_index=True)
    st.bar_chart(df_daily.set_index("Data")["Incasso"])

with col2:
    st.subheader("Riepilogo mensile")
    df_monthly = pd.DataFrame(monthly_revenue)
    df_monthly = df_monthly.rename(columns={"month": "Mese", "revenue": "Incasso"})
    st.dataframe(df_monthly, hide_index=True)
    st.bar_chart(df_monthly.set_index("Mese")["Incasso"])

st.markdown("---")
st.subheader("Filtra per periodo")
period = st.selectbox("Periodo", ["Settimana", "Mese", "Trimestre", "Anno"])
st.info(f"Filtro applicato: {period} (demo)")