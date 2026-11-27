from datetime import time
import pandas as pd
import streamlit as st
from sqlalchemy.exc import IntegrityError
from db.database import get_session, init_db
from services.collaborator_service import (
    DEFAULT_WORK_DAYS,
    create_collaborator,
    delete_collaborator,
    deserialize_work_days,
    get_collaborators,
    update_collaborator,
)

init_db()

DAYS_OPTIONS = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
ROLE_OPTIONS = ["Barbiere", "Apprendista", "Barbiere capo"]

st.subheader("Collaboratori")

tab_list, tab_new, tab_edit = st.tabs(
    ["Elenco", "Nuovo collaboratore", "Modifica collaboratore / orari"]
)

try:
    with get_session() as session:
        collaborators = get_collaborators(session)
except Exception as exc:
    st.error(f"Errore nel caricamento dei collaboratori: {exc}")
    collaborators = []

with tab_list:
    if collaborators:
        rows = [
            {
                "ID": c.id,
                "Nome": c.name,
                "Ruolo": c.role,
                "Disponibile": bool(c.availability),
                "Inizio turno": c.start_time.strftime("%H:%M"),
                "Fine turno": c.end_time.strftime("%H:%M"),
                "Giorni lavorativi": ", ".join(deserialize_work_days(c.work_days)),
            }
            for c in collaborators
        ]
        df = pd.DataFrame(rows)
        st.dataframe(df, hide_index=True, width="stretch")
    else:
        st.info("Nessun collaboratore registrato.")

with tab_new:
    st.subheader("Nuovo collaboratore")
    with st.form("new_collab_form"):
        name = st.text_input("Nome *")
        role = st.selectbox("Ruolo", ROLE_OPTIONS)
        available = st.checkbox("Disponibile", value=True)
        col1, col2 = st.columns(2)
        start_t = col1.time_input("Inizio turno", value=time(9, 0))
        end_t = col2.time_input("Fine turno", value=time(18, 0))
        work_days = st.multiselect(
            "Giorni lavorativi",
            options=DAYS_OPTIONS,
            default=DEFAULT_WORK_DAYS,
        )
        submitted = st.form_submit_button("Salva")
        if submitted:
            if not name.strip():
                st.error("Nome è obbligatorio.")
            elif start_t >= end_t:
                st.error("L'orario di inizio turno deve essere precedente alla fine turno.")
            else:
                try:
                    with get_session() as session:
                        create_collaborator(
                            session,
                            name=name,
                            role=role,
                            availability=available,
                            start_time=start_t,
                            end_time=end_t,
                            work_days=work_days,
                        )
                    st.success("Collaboratore salvato nel database.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Errore durante il salvataggio: {exc}")

with tab_edit:
    st.subheader("Modifica collaboratore / orari")
    if collaborators:
        current = st.selectbox(
            "Seleziona collaboratore",
            options=collaborators,
            format_func=lambda c: f"{c.name} ({c.role})",
            key="edit_collab_select",
        )
        if current:
            current_days = deserialize_work_days(current.work_days)
            role_idx = ROLE_OPTIONS.index(current.role) if current.role in ROLE_OPTIONS else 0
            with st.form(f"edit_collab_form_{current.id}"):
                e_name = st.text_input("Nome *", value=current.name)
                e_role = st.selectbox("Ruolo", ROLE_OPTIONS, index=role_idx)
                e_available = st.checkbox("Disponibile", value=bool(current.availability))
                col1, col2 = st.columns(2)
                e_start = col1.time_input("Inizio turno", value=current.start_time)
                e_end = col2.time_input("Fine turno", value=current.end_time)
                e_work_days = st.multiselect(
                    "Giorni lavorativi",
                    options=DAYS_OPTIONS,
                    default=[d for d in current_days if d in DAYS_OPTIONS],
                )
                b_col1, b_col2 = st.columns(2)
                submitted = b_col1.form_submit_button("Salva modifiche")
                deleted_btn = b_col2.form_submit_button("Elimina collaboratore")

                if submitted:
                    if not e_name.strip():
                        st.error("Nome è obbligatorio.")
                    elif e_start >= e_end:
                        st.error("L'orario di inizio turno deve essere precedente alla fine turno.")
                    else:
                        try:
                            with get_session() as session:
                                update_collaborator(
                                    session,
                                    collaborator_id=current.id,
                                    name=e_name,
                                    role=e_role,
                                    availability=e_available,
                                    start_time=e_start,
                                    end_time=e_end,
                                    work_days=e_work_days,
                                )
                            st.success("Collaboratore aggiornato nel database.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Errore durante l'aggiornamento: {exc}")

                if deleted_btn:
                    try:
                        with get_session() as session:
                            delete_collaborator(session, current.id)
                        st.success("Collaboratore eliminato.")
                        st.rerun()
                    except IntegrityError:
                        st.error("Impossibile eliminare il collaboratore: esistono appuntamenti associati.")
                    except Exception as exc:
                        st.error(f"Errore durante l'eliminazione: {exc}")
    else:
        st.info("Nessun collaboratore disponibile da modificare.")
