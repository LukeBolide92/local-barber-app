import streamlit as st
import pandas as pd

st.title("Clienti")

# Init session_state demo data
if "clients_data" not in st.session_state:
    st.session_state.clients_data = [
        {"id": 1, "name": "Mario Rossi", "phone": "333123456", "email": "mario@email.com"},
        {"id": 2, "name": "Luca Verdi", "phone": "333654321", "email": "luca@email.com"},
        {"id": 3, "name": "Giulia Bianchi", "phone": "333789012", "email": "giulia@email.com"},
        {"id": 4, "name": "Antonio Neri", "phone": "333456789", "email": "antonio@email.com"},
        {"id": 5, "name": "Sara Gialli", "phone": "333987654", "email": "sara@email.com"},
        {"id": 6, "name": "Marco Blu", "phone": "333246810", "email": "marco@email.com"},
        {"id": 7, "name": "Laura Viola", "phone": "333135791", "email": "laura@email.com"},
        {"id": 8, "name": "Roberto Arancio", "phone": "333864209", "email": "roberto@email.com"},
        {"id": 9, "name": "Elena Rosa", "phone": "333741852", "email": "elena@email.com"},
        {"id": 10, "name": "Davide Grigio", "phone": "333963852", "email": "davide@email.com"},
    ]
    st.session_state.next_client_id = 11

clients = st.session_state.clients_data

tab_list, tab_new, tab_edit = st.tabs(["Elenco", "Nuovo cliente", "Modifica cliente"])

with tab_list:
    search = st.text_input("Cerca per nome, telefono o email")
    if search:
        filtered = [c for c in clients if search.lower() in c["name"].lower() or search in c["phone"] or search.lower() in c["email"].lower()]
    else:
        filtered = clients

    df = pd.DataFrame(filtered)
    if not df.empty:
        df = df.rename(columns={
            "id": "ID",
            "name": "Nome",
            "phone": "Telefono",
            "email": "Email",
        })
        st.dataframe(df, hide_index=True)
        st.caption(f"{len(filtered)} clienti trovati")
    else:
        st.info("Nessun cliente trovato.")

with tab_new:
    st.subheader("Nuovo cliente")
    with st.form("new_client_form"):
        name = st.text_input("Nome *")
        phone = st.text_input("Telefono *")
        email = st.text_input("Email")
        submitted = st.form_submit_button("Salva")
        if submitted:
            if name and phone:
                st.session_state.clients_data.append({
                    "id": st.session_state.next_client_id,
                    "name": name,
                    "phone": phone,
                    "email": email,
                })
                st.session_state.next_client_id += 1
                st.success("Cliente creato (demo).")
                st.rerun()
            else:
                st.error("Nome e telefono sono obbligatori.")

with tab_edit:
    st.subheader("Modifica cliente")
    if clients:
        selected_name = st.selectbox(
            "Seleziona cliente",
            options=[c["name"] for c in clients],
            key="edit_client_select"
        )
        current = next((c for c in clients if c["name"] == selected_name), None)
        if current:
            with st.form("edit_client_form"):
                e_name = st.text_input("Nome *", value=current["name"])
                e_phone = st.text_input("Telefono *", value=current["phone"])
                e_email = st.text_input("Email", value=current["email"])
                submitted = st.form_submit_button("Salva modifiche")
                if submitted:
                    if e_name and e_phone:
                        for c in st.session_state.clients_data:
                            if c["id"] == current["id"]:
                                c["name"] = e_name
                                c["phone"] = e_phone
                                c["email"] = e_email
                                break
                        st.success("Cliente aggiornato (demo).")
                        st.rerun()
                    else:
                        st.error("Nome e telefono sono obbligatori.")
    else:
        st.info("Nessun cliente disponibile da modificare.")