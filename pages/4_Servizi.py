import streamlit as st
import pandas as pd

st.title("Servizi")

# Init session_state demo data
if "services_data" not in st.session_state:
    st.session_state.services_data = [
        {"id": 1, "name": "Taglio", "duration_minutes": 30, "price": 18.0},
        {"id": 2, "name": "Barba", "duration_minutes": 20, "price": 12.0},
        {"id": 3, "name": "Taglio + Barba", "duration_minutes": 45, "price": 25.0},
        {"id": 4, "name": "Colorazione", "duration_minutes": 60, "price": 55.0},
        {"id": 5, "name": "Rasatura", "duration_minutes": 15, "price": 10.0},
        {"id": 6, "name": "Trattamento capelli", "duration_minutes": 25, "price": 20.0},
    ]
    st.session_state.next_service_id = 7

services = st.session_state.services_data

tab_list, tab_new, tab_edit = st.tabs(["Elenco", "Nuovo servizio", "Modifica servizio"])

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
                st.session_state.services_data.append({
                    "id": st.session_state.next_service_id,
                    "name": name,
                    "duration_minutes": int(duration),
                    "price": float(price),
                })
                st.session_state.next_service_id += 1
                st.success("Servizio creato (demo).")
                st.rerun()
            else:
                st.error("Nome è obbligatorio.")

with tab_edit:
    st.subheader("Modifica servizio")
    if services:
        selected_name = st.selectbox(
            "Seleziona servizio",
            options=[s["name"] for s in services],
            key="edit_service_select"
        )
        current = next((s for s in services if s["name"] == selected_name), None)
        if current:
            with st.form("edit_service_form"):
                e_name = st.text_input("Nome *", value=current["name"])
                e_duration = st.number_input("Durata (min)", min_value=5, max_value=180, value=current["duration_minutes"])
                e_price = st.number_input("Prezzo (€)", min_value=0.0, value=current["price"])
                submitted = st.form_submit_button("Salva modifiche")
                if submitted:
                    if e_name:
                        for s in st.session_state.services_data:
                            if s["id"] == current["id"]:
                                s["name"] = e_name
                                s["duration_minutes"] = int(e_duration)
                                s["price"] = float(e_price)
                                break
                        st.success("Servizio aggiornato (demo).")
                        st.rerun()
                    else:
                        st.error("Nome è obbligatorio.")
    else:
        st.info("Nessun servizio disponibile da modificare.")