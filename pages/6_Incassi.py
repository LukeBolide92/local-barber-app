import pandas as pd
import streamlit as st
from database import get_session, init_db
from services.revenue_service import (
    get_daily_revenue,
    get_monthly_revenue,
    get_period_revenue_total,
)

init_db()

st.title("Incassi")

try:
    with get_session() as session:
        daily_revenue = get_daily_revenue(session, days=7)
        monthly_revenue = get_monthly_revenue(session, months=6)
except Exception as exc:
    st.error(f"Errore nel caricamento degli incassi: {exc}")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    st.subheader("Riepilogo giornaliero (ultimi 7 giorni)")
    df_daily = pd.DataFrame(daily_revenue)
    df_daily = df_daily.rename(columns={"date": "Data", "revenue": "Incasso"})
    st.dataframe(
        df_daily,
        column_config={"Incasso": st.column_config.NumberColumn("Incasso", format="€ %.2f")},
        hide_index=True,
        width="stretch",
    )
    st.bar_chart(df_daily.set_index("Data")["Incasso"])

with col2:
    st.subheader("Riepilogo mensile (ultimi 6 mesi)")
    df_monthly = pd.DataFrame(monthly_revenue)
    df_monthly = df_monthly.rename(columns={"month": "Mese", "revenue": "Incasso"})
    st.dataframe(
        df_monthly,
        column_config={"Incasso": st.column_config.NumberColumn("Incasso", format="€ %.2f")},
        hide_index=True,
        width="stretch",
    )
    st.bar_chart(df_monthly.set_index("Mese")["Incasso"])

st.markdown("---")
st.subheader("Riepilogo per periodo")
period = st.selectbox("Periodo", ["Settimana", "Mese", "Trimestre", "Anno"])

try:
    with get_session() as session:
        total_rev, appt_count = get_period_revenue_total(session, period)
    m_col1, m_col2 = st.columns(2)
    m_col1.metric(f"Incasso ({period})", f"€ {total_rev:.2f}")
    m_col2.metric(f"Appuntamenti ({period})", appt_count)
except Exception as exc:
    st.error(f"Errore nel calcolo del riepilogo per periodo: {exc}")
