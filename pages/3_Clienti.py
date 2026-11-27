import pandas as pd
import streamlit as st
from sqlalchemy.exc import IntegrityError
from db.database import get_session, init_db
from services.client_service import (
    create_client,
    delete_client,
    get_clients,
    search_clients,
    update_client,
)

init_db()

st.subheader("Clienti")

tab_list, tab_new, tab_edit = st.tabs(["Elenco", "Nuovo cliente", "Modifica cliente"])

with tab_list:
    search = st.text_input("Cerca per nome, telefono o email")
    try:
        with get_session() as session:
            clients = search_clients(session, search) if search.strip() else get_clients(session)
    except Exception as exc:
        st.error(f"Errore nel caricamento dei clienti: {exc}")
        clients = []

    if clients:
        rows = [
            {
                "ID": c.id,
                "Nome": c.name,
                "Telefono": c.phone,
                "Email": c.email or "",
            }
            for c in clients
        ]
        df = pd.DataFrame(rows)
        st.dataframe(df, hide_index=True, width="stretch")
        st.caption(f"{len(clients)} clienti trovati")
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
            if not name.strip() or not phone.strip():
                st.error("Nome e telefono sono obbligatori.")
            else:
                try:
                    with get_session() as session:
                        create_client(session, name, phone, email)
                    st.success("Cliente salvato nel database.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Errore durante il salvataggio del cliente: {exc}")

with tab_edit:
    st.subheader("Modifica cliente")
    try:
        with get_session() as session:
            all_clients = get_clients(session)
    except Exception as exc:
        st.error(f"Errore nel caricamento dei clienti: {exc}")
        all_clients = []

    if all_clients:
        current = st.selectbox(
            "Seleziona cliente",
            options=all_clients,
            format_func=lambda c: f"{c.name} ({c.phone})",
            key="edit_client_select",
        )
        if current:
            with st.form(f"edit_client_form_{current.id}"):
                e_name = st.text_input("Nome *", value=current.name)
                e_phone = st.text_input("Telefono *", value=current.phone)
                e_email = st.text_input("Email", value=current.email or "")
                col1, col2 = st.columns(2)
                submitted = col1.form_submit_button("Salva modifiche")
                deleted_btn = col2.form_submit_button("Elimina cliente")

                if submitted:
                    if not e_name.strip() or not e_phone.strip():
                        st.error("Nome e telefono sono obbligatori.")
                    else:
                        try:
                            with get_session() as session:
                                update_client(session, current.id, e_name, e_phone, e_email)
                            st.success("Cliente aggiornato nel database.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Errore durante l'aggiornamento: {exc}")

                if deleted_btn:
                    try:
                        with get_session() as session:
                            delete_client(session, current.id)
                        st.success("Cliente eliminato.")
                        st.rerun()
                    except IntegrityError:
                        st.error("Impossibile eliminare il cliente: esistono appuntamenti associati.")
                    except Exception as exc:
                        st.error(f"Errore durante l'eliminazione: {exc}")
    else:
        st.info("Nessun cliente disponibile da modificare.")
