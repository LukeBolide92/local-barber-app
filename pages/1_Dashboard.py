from datetime import date
import pandas as pd
import streamlit as st
from db.database import get_session, init_db
from services.appointment_service import get_appointments_by_date, get_revenue_summary
from services.revenue_service import (
    get_top_services,
    get_pending_payments,
    get_refunds,
)

init_db()

st.subheader("Appuntamenti di oggi")

try:
    with get_session() as session:
        appointments_today = get_appointments_by_date(session, date.today())
        summary = get_revenue_summary(session)
        top_services = get_top_services(session, period="Mese", limit=5)
        pending_payments = get_pending_payments(session, period="Mese")
        refunds = get_refunds(session, period="Mese")
except Exception as exc:
    st.error(f"Errore nel caricamento della dashboard: {exc}")
    st.stop()

if appointments_today:
    rows = [
        {
            "id": a.id,
            "client": a.client.name if a.client else "-",
            "service": a.service.name if a.service else "-",
            "collaborator": a.collaborator.name if a.collaborator else "-",
            "time": a.time.strftime("%H:%M"),
            "price": float(a.service.price) if a.service else 0.0,
        }
        for a in appointments_today
    ]
    df_appointments = pd.DataFrame(rows)
    st.dataframe(
        df_appointments,
        column_config={
            "id": st.column_config.NumberColumn("ID", width=50),
            "client": "Cliente",
            "service": "Servizio",
            "collaborator": "Collaboratore",
            "time": "Orario",
            "price": st.column_config.NumberColumn("Prezzo", format="€ %.2f"),
        },
        hide_index=True,
        width="stretch",
    )
else:
    st.info("Nessun appuntamento programmato per oggi.")

st.markdown("---")
col1, col2, col3 = st.columns(3)
col1.metric("Incassi oggi", f"€ {summary['today']:.2f}")
col2.metric("Incassi mese", f"€ {summary['month']:.2f}")
col3.metric("Appuntamenti oggi", summary["today_count"])

st.markdown("---")
col4, col5, col6 = st.columns(3)
col4.metric("Servizi completati oggi", summary.get("today_completed_count", 0))
col5.metric("Pagamenti da registrare (mese)", f"€ {pending_payments:.2f}")
col6.metric("Rimborsi (mese)", f"€ {refunds:.2f}")

st.markdown("---")
st.subheader("Servizi più venduti (mese)")

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
