import streamlit as st
from database import init_db

st.set_page_config(
    page_title="Local Barber Manager",
    page_icon="✂️",
    layout="wide",
)

init_db()

pg = st.navigation([
    st.Page("pages/1_Dashboard.py", title="Dashboard", default=True),
    st.Page("pages/2_Appuntamenti.py", title="Appuntamenti"),
    st.Page("pages/3_Clienti.py", title="Clienti"),
    st.Page("pages/4_Servizi.py", title="Servizi"),
    st.Page("pages/5_Collaboratori.py", title="Collaboratori"),
    st.Page("pages/6_Incassi.py", title="Incassi"),
    st.Page("pages/7_Impostazioni.py", title="Impostazioni"),
])

pg.run()
