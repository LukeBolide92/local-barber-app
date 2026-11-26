from datetime import date
import pandas as pd
import streamlit as st
from database import get_session, init_db
from services.appointment_service import get_appointments_by_date, get_revenue_summary

init_db()

st.title("Local Barber Manager ✂️")
st.subheader("Appuntamenti di oggi")

try:
    with get_session() as session:
        appointments_today = get_appointments_by_date(session, date.today())
        summary = get_revenue_summary(session)
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
