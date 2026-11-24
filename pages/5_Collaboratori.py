import streamlit as st
import pandas as pd
from datetime import time

st.title("Collaboratori")

# Init session_state demo data
if "collaborators_data" not in st.session_state:
    st.session_state.collaborators_data = [
        {"id": 1, "name": "Marco", "role": "Barbiere", "availability": True, "start_time": time(9, 0), "end_time": time(18, 0), "work_days": ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"]},
        {"id": 2, "name": "Paolo", "role": "Barbiere", "availability": True, "start_time": time(10, 0), "end_time": time(19, 0), "work_days": ["Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato"]},
        {"id": 3, "name": "Luca", "role": "Apprendista", "availability": False, "start_time": time(9, 0), "end_time": time(13, 0), "work_days": ["Lunedì", "Martedì", "Mercoledì", "Giovedì"]},
    ]
    st.session_state.next_collab_id = 4

collaborators = st.session_state.collaborators_data

tab_list, tab_new, tab_edit = st.tabs(["Elenco", "Nuovo collaboratore", "Modifica collaboratore / orari"])

with tab_list:
    df = pd.DataFrame(collaborators)
    df = df.rename(columns={
        "id": "ID",
        "name": "Nome",
        "role": "Ruolo",
        "availability": "Disponibile",
    })
    st.dataframe(df, hide_index=True)

with tab_new:
    st.subheader("Nuovo collaboratore")
    with st.form("new_collab_form"):
        name = st.text_input("Nome *")
        role = st.selectbox("Ruolo", ["Barbiere", "Apprendista", "Barbiere capo"])
        available = st.checkbox("Disponibile", value=True)
        submitted = st.form_submit_button("Salva")
        if submitted:
            if name:
                st.session_state.collaborators_data.append({
                    "id": st.session_state.next_collab_id,
                    "name": name,
                    "role": role,
                    "availability": available,
                    "start_time": time(9, 0),
                    "end_time": time(18, 0),
                    "work_days": ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"],
                })
                st.session_state.next_collab_id += 1
                st.success("Collaboratore creato (demo).")
                st.rerun()
            else:
                st.error("Nome è obbligatorio.")

with tab_edit:
    st.subheader("Modifica collaboratore / orari")
    if collaborators:
        selected_name = st.selectbox(
            "Seleziona collaboratore",
            options=[c["name"] for c in collaborators],
            key="edit_collab_select"
        )
        current = next((c for c in collaborators if c["name"] == selected_name), None)
        if current:
            with st.form("edit_collab_form"):
                e_available = st.checkbox("Disponibile", value=current["availability"])
                e_start = st.time_input("Inizio turno", value=current["start_time"])
                e_end = st.time_input("Fine turno", value=current["end_time"])
                e_work_days = st.multiselect(
                    "Giorni lavorativi",
                    options=["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"],
                    default=current["work_days"],
                )
                submitted = st.form_submit_button("Salva modifiche")
                if submitted:
                    for c in st.session_state.collaborators_data:
                        if c["id"] == current["id"]:
                            c["availability"] = e_available
                            c["start_time"] = e_start
                            c["end_time"] = e_end
                            c["work_days"] = e_work_days
                            break
                    st.success("Collaboratore aggiornato (demo).")
                    st.rerun()
    else:
        st.info("Nessun collaboratore disponibile da modificare.")