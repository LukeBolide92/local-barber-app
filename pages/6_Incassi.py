import pandas as pd
import streamlit as st
from db.database import get_session, init_db
from services.revenue_service import (
    get_daily_revenue,
    get_monthly_revenue,
    get_period_revenue_total,
    get_top_services,
    get_pending_payments,
    get_refunds,
    get_revenue_month,
)

from utils.page_header import render_page_header

init_db()

st.subheader("Incassi")

try:
    with get_session() as session:
        daily_revenue = get_daily_revenue(session, days=7)
        monthly_revenue = get_monthly_revenue(session, months=7)
        top_services = get_top_services(session, period="Mese", limit=5)
        pending_payments = get_pending_payments(session, period="Mese")
        refunds = get_refunds(session, period="Mese")
except Exception as exc:
    st.error(f"Errore nel caricamento degli incassi: {exc}")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    render_page_header("Riepilogo giornaliero (ultimi 7 giorni)")
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
    render_page_header("Riepilogo mensile (ultimi 7 mesi)")
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
render_page_header("Riepilogo per periodo")
period = st.selectbox("Periodo", ["Settimana", "Mese", "Trimestre", "Anno"])

try:
    with get_session() as session:
        total_rev, appt_count = get_period_revenue_total(session, period)
    m_col1, m_col2 = st.columns(2)
    m_col1.metric(f"Incasso ({period})", f"€ {total_rev:.2f}")
    m_col2.metric(f"Appuntamenti ({period})", appt_count)
except Exception as exc:
    st.error(f"Errore nel calcolo del riepilogo per periodo: {exc}")

st.markdown("---")
render_page_header("Servizi più venduti (mese)")
if top_services:
    df_top = pd.DataFrame(top_services)
    st.dataframe(
        df_top,
        column_config={
            "revenue": st.column_config.NumberColumn("Ricavo", format="€ %.2f"),
            "count": st.column_config.NumberColumn("Servizi", format="%.0f"),
        },
        hide_index=True,
        width="stretch",
    )
else:
    st.info("Nessun servizio venduto nel periodo corrente.")

st.markdown("---")
render_page_header("Pagamenti e rimborsi")
col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    st.metric("Pagamenti da registrare (mese)", f"€ {pending_payments:.2f}")
with col_p2:
    st.metric("Rimborsi (mese)", f"€ {refunds:.2f}")
with col_p3:
    st.metric("Incasso mese (netto)", f"€ {get_revenue_month(session):.2f}")

st.markdown("---")
render_page_header("Riepilogo pagamenti per periodo")
period2 = st.selectbox("Periodo pagamenti", ["Settimana", "Mese", "Trimestre", "Anno"], key="incass_period_payments")
try:
    with get_session() as session:
        pending = get_pending_payments(session, period=period2)
        refunds_p = get_refunds(session, period=period2)
    n_col1, n_col2 = st.columns(2)
    n_col1.metric(f"Pagamenti da registrare ({period2})", f"€ {pending:.2f}")
    n_col2.metric(f"Rimborsi ({period2})", f"€ {refunds_p:.2f}")
except Exception as exc:
    st.error(f"Errore nel calcolo pagamenti per periodo: {exc}")
