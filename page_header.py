import streamlit as st


def render_page_header(title: str, font_size: str = "1.1rem", font_weight: str = "600") -> None:
    """Renderizza un titolo di pagina/section come markdown con font size e weight personalizzabili.

    Metodo comune per i titoli delle schermate: permette di cambiare globalmente
    la dimensione (font_size) e il grassetto (font_weight) del titolo.
    """
    st.markdown(
        f"<div style='font-size: {font_size}; font-weight: {font_weight};'>{title}</div>",
        unsafe_allow_html=True,
    )
