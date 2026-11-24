import streamlit as st
import pandas as pd

# Demo data
appointments_today = [
    {"id": 1, "client": "Mario Rossi", "service": "Taglio + Barba", "time": "09:00", "price": 25.0},
    {"id": 2, "client": "Luca Verdi", "service": "Taglio", "time": "10:30", "price": 18.0},
    {"id": 3, "client": "Giulia Bianchi", "service": "Colorazione", "time": "14:00", "price": 55.0},
    {"id": 4, "client": "Mario Rossi", "service": "Barba", "time": "15:30", "price": 12.0},
    {"id": 5, "client": "Giulia Bianchi", "service": "Taglio", "time": "16:30", "price": 18.0},
]
revenue_today = sum(a["price"] for a in appointments_today)
revenue_this_month = 2450.0

st.title("Dashboard")
st.subheader("Appuntamenti di oggi")

df_appointments = pd.DataFrame(appointments_today)
st.dataframe(
    df_appointments,
    column_config={
        "id": st.column_config.NumberColumn("ID", width=50),
        "client": "Cliente",
        "service": "Servizio",
        "time": "Orario",
        "price": st.column_config.NumberColumn("Prezzo", format="€ %.2f"),
    },
    hide_index=True,
)

st.markdown("---")
col1, col2, col3 = st.columns(3)
col1.metric("Incassi oggi", f"€ {revenue_today:.2f}")
col2.metric("Incassi mese", f"€ {revenue_this_month:.2f}")
col3.metric("Appuntamenti totali", len(appointments_today))