import streamlit as st
import pandas as pd

st.title("Collaboratori")

# Demo data
collaborators = [
    {"id": 1, "name": "Marco", "role": "Barbiere", "availability": True},
    {"id": 2, "name": "Paolo", "role": "Barbiere", "availability": True},
    {"id": 3, "name": "Luca", "role": "Apprendista", "availability": False},
]

tab_list, tab_new = st.tabs(["Elenco", "Nuovo collaboratore"])

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
                st.success("Collaboratore creato (demo).")
            else:
                st.error("Nome è obbligatorio.")