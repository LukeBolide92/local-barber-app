import streamlit as st
import pandas as pd
from datetime import date, time, datetime

st.title("Appuntamenti")

# Demo data
all_appointments = [
    {"id": 1, "date": date(2025, 1, 15), "client": "Mario Rossi", "service": "Taglio + Barba", "collaborator": "Marco", "time": "09:00"},
    {"id": 2, "date": date(2025, 1, 15), "client": "Luca Verdi", "service": "Taglio", "collaborator": "Paolo", "time": "10:30"},
    {"id": 3, "date": date(2025, 1, 16), "client": "Giulia Bianchi", "service": "Colorazione", "collaborator": "Marco", "time": "14:00"},
    {"id": 4, "date": date(2025, 1, 17), "client": "Mario Rossi", "service": "Barba", "collaborator": "Paolo", "time": "15:30"},
    {"id": 5, "date": date(2025, 1, 17), "client": "Giulia Bianchi", "service": "Taglio", "collaborator": "Marco", "time": "16:30"},
]

clients = [
    {"id": 1, "name": "Mario Rossi"},
    {"id": 2, "name": "Luca Verdi"},
    {"id": 3, "name": "Giulia Bianchi"},
]
services = [
    {"id": 1, "name": "Taglio", "duration": 30, "price": 18.0},
    {"id": 2, "name": "Barba", "duration": 20, "price": 12.0},
    {"id": 3, "name": "Taglio + Barba", "duration": 45, "price": 25.0},
    {"id": 4, "name": "Colorazione", "duration": 60, "price": 55.0},
]
collaborators = [
    {"id": 1, "name": "Marco"},
    {"id": 2, "name": "Paolo"},
]

tab_list, tab_new = st.tabs(["Elenco", "Nuovo appuntamento"])

with tab_list:
    st.subheader("Filtri")
    col1, col2 = st.columns(2)
    with col1:
        filter_date = st.date_input("Data", value=date.today())
    with col2:
        filter_collab = st.selectbox("Collaboratore", ["Tutti"] + [c["name"] for c in collaborators])

    filtered = [a for a in all_appointments if a["date"] == filter_date]
    if filter_collab != "Tutti":
        filtered = [a for a in filtered if a["collaborator"] == filter_collab]

    if filtered:
        df = pd.DataFrame(filtered)
        df = df.rename(columns={
            "id": "ID",
            "date": "Data",
            "client": "Cliente",
            "service": "Servizio",
            "collaborator": "Collaboratore",
            "time": "Orario",
        })
        st.dataframe(df, hide_index=True)
    else:
        st.info("Nessun appuntamento per i filtri selezionati.")

with tab_new:
    st.subheader("Nuovo appuntamento")
    with st.form("new_appointment_form"):
        client = st.selectbox("Cliente", [c["name"] for c in clients])
        service = st.selectbox("Servizio", [s["name"] for s in services])
        collaborator = st.selectbox("Collaboratore", [c["name"] for c in collaborators])
        appt_date = st.date_input("Data", value=date.today())
        appt_time = st.time_input("Orario", value=time(9, 0))
        notes = st.text_area("Note", height=80)
        submitted = st.form_submit_button("Salva")
        if submitted:
            st.success("Appuntamento creato (demo).")
            st.rerun()