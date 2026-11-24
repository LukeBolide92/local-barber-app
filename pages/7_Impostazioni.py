import os
import streamlit as st
from database import DB_PATH, get_session, init_db
from services.appointment_service import get_appointments
from services.client_service import get_clients
from services.collaborator_service import get_collaborators
from services.service import get_services

init_db()

st.title("Impostazioni")

st.subheader("Stato Database")
db_exists = os.path.exists(DB_PATH)
db_size_kb = os.path.getsize(DB_PATH) / 1024 if db_exists else 0.0

col1, col2 = st.columns(2)
col1.text_input("Percorso database attivo", value=os.path.abspath(DB_PATH), disabled=True)
col2.metric("Dimensione database", f"{db_size_kb:.1f} KB" if db_exists else "Non trovato")

try:
    with get_session() as session:
        n_clients = len(get_clients(session))
        n_services = len(get_services(session))
        n_collabs = len(get_collaborators(session))
        n_appts = len(get_appointments(session))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Clienti", n_clients)
    c2.metric("Servizi", n_services)
    c3.metric("Collaboratori", n_collabs)
    c4.metric("Appuntamenti", n_appts)
except Exception as exc:
    st.error(f"Errore nella lettura delle statistiche del database: {exc}")

st.markdown("---")
st.subheader("Backup")
st.info("La funzionalità di backup e ripristino automatico sarà implementata nella FASE 5.")

st.markdown("---")
st.subheader("Informazioni")
st.write("Barber Manager - Versione 0.3 (FASE 3 - Persistenza SQLite attiva)")
