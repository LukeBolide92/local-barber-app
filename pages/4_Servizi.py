import streamlit as st
import pandas as pd

st.title("Servizi")

# Demo data
services = [
    {"id": 1, "name": "Taglio", "duration_minutes": 30, "price": 18.0},
    {"id": 2, "name": "Barba", "duration_minutes": 20, "price": 12.0},
    {"id": 3, "name": "Taglio + Barba", "duration_minutes": 45, "price": 25.0},
    {"id": 4, "name": "Colorazione", "duration_minutes": 60, "price": 55.0},
    {"id": 5, "name": "Rasatura", "duration_minutes": 15, "price": 10.0},
    {"id": 6, "name": "Trattamento capelli", "duration_minutes": 25, "price": 20.0},
]

tab_list, tab_new = st.tabs(["Elenco", "Nuovo servizio"])

with tab_list:
    df = pd.DataFrame(services)
    df = df.rename(columns={
        "id": "ID",
        "name": "Servizio",
        "duration_minutes": "Durata (min)",
        "price": "Prezzo",
    })
    st.dataframe(df, hide_index=True)

with tab_new:
    st.subheader("Nuovo servizio")
    with st.form("new_service_form"):
        name = st.text_input("Nome *")
        duration = st.number_input("Durata (min)", min_value=5, max_value=180, value=30)
        price = st.number_input("Prezzo (€)", min_value=0.0, value=10.0)
        submitted = st.form_submit_button("Salva")
        if submitted:
            if name:
                st.success("Servizio creato (demo).")
            else:
                st.error("Nome è obbligatorio.")