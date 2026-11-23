import streamlit as st

st.title("Impostazioni")

st.subheader("Backup")
st.write("Esegui un backup del database.")
if st.button("Crea backup", type="primary"):
    st.success("Backup creato (demo).")

st.markdown("---")
st.subheader("Database")
db_path = st.text_input("Percorso database", value="barber.db")
if st.button("Salva percorso"):
    st.success("Percorso salvato (demo).")

st.markdown("---")
st.subheader("Tema")
theme = st.selectbox("Tema", ["Sistema", "Chiaro", "Scuro"])
st.info(f"Tema selezionato: {theme} (demo)")

st.markdown("---")
st.subheader("Informazioni")
st.write("Barber Manager - Versione 0.1 (FASE 1)")