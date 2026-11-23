import streamlit as st
import pandas as pd

st.title("Clienti")

# Demo data
clients = [
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

tab_list, tab_new = st.tabs(["Elenco", "Nuovo cliente"])

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
                st.success("Cliente creato (demo).")
            else:
                st.error("Nome e telefono sono obbligatori.")