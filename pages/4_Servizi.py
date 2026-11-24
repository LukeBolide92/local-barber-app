import pandas as pd
import streamlit as st
from sqlalchemy.exc import IntegrityError
from database import get_session, init_db
from services.service import (
    create_service,
    delete_service,
    get_services,
    update_service,
)

init_db()

st.title("Servizi")

tab_list, tab_new, tab_edit = st.tabs(["Elenco", "Nuovo servizio", "Modifica servizio"])

try:
    with get_session() as session:
        services = get_services(session)
except Exception as exc:
    st.error(f"Errore nel caricamento dei servizi: {exc}")
    services = []

with tab_list:
    if services:
        rows = [
            {
                "ID": s.id,
                "Servizio": s.name,
                "Durata (min)": s.duration_minutes,
                "Prezzo": float(s.price),
            }
            for s in services
        ]
        df = pd.DataFrame(rows)
        st.dataframe(
            df,
            column_config={
                "Prezzo": st.column_config.NumberColumn("Prezzo", format="€ %.2f"),
            },
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("Nessun servizio registrato.")

with tab_new:
    st.subheader("Nuovo servizio")
    with st.form("new_service_form"):
        name = st.text_input("Nome *")
        duration = st.number_input("Durata (min)", min_value=5, max_value=180, value=30, step=5)
        price = st.number_input("Prezzo (€)", min_value=0.0, value=15.0, step=1.0)
        submitted = st.form_submit_button("Salva")
        if submitted:
            if not name.strip():
                st.error("Nome è obbligatorio.")
            else:
                try:
                    with get_session() as session:
                        create_service(session, name, int(duration), float(price))
                    st.success("Servizio salvato nel database.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Errore durante il salvataggio: {exc}")

with tab_edit:
    st.subheader("Modifica servizio")
    if services:
        current = st.selectbox(
            "Seleziona servizio",
            options=services,
            format_func=lambda s: f"{s.name} (€ {s.price:.2f})",
            key="edit_service_select",
        )
        if current:
            with st.form(f"edit_service_form_{current.id}"):
                e_name = st.text_input("Nome *", value=current.name)
                e_duration = st.number_input(
                    "Durata (min)",
                    min_value=5,
                    max_value=180,
                    value=int(current.duration_minutes),
                    step=5,
                )
                e_price = st.number_input(
                    "Prezzo (€)",
                    min_value=0.0,
                    value=float(current.price),
                    step=1.0,
                )
                col1, col2 = st.columns(2)
                submitted = col1.form_submit_button("Salva modifiche")
                deleted_btn = col2.form_submit_button("Elimina servizio")

                if submitted:
                    if not e_name.strip():
                        st.error("Nome è obbligatorio.")
                    else:
                        try:
                            with get_session() as session:
                                update_service(
                                    session,
                                    current.id,
                                    e_name,
                                    int(e_duration),
                                    float(e_price),
                                )
                            st.success("Servizio aggiornato nel database.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Errore durante l'aggiornamento: {exc}")

                if deleted_btn:
                    try:
                        with get_session() as session:
                            delete_service(session, current.id)
                        st.success("Servizio eliminato.")
                        st.rerun()
                    except IntegrityError:
                        st.error("Impossibile eliminare il servizio: esistono appuntamenti associati.")
                    except Exception as exc:
                        st.error(f"Errore durante l'eliminazione: {exc}")
    else:
        st.info("Nessun servizio disponibile da modificare.")
