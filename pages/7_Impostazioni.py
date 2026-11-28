import os
import tempfile
from pathlib import Path
import pandas as pd
import streamlit as st
from db.database import DB_PATH, get_session, init_db
from services.appointment_service import get_appointments
from services.backup_service import (
    DEFAULT_BACKUP_DIR,
    create_backup,
    delete_backup,
    list_backups,
    restore_backup,
)
from services.client_service import get_clients
from services.collaborator_service import get_collaborators
from services.service import get_services
from services.supabase_credential_service import (
    CredentialStoreUnavailableError,
    delete_pat,
    store_pat,
)

from utils.page_header import render_page_header
from utils.supabase import extract_project_ref

init_db()

st.subheader("Impostazioni")

tab_locale, tab_remota = st.tabs(["Database locale", "Database remoto"])

with tab_locale:
    st.info("Configura il tuo gestionale per il salvataggio locale dei tuoi dati")
    with st.expander("Configura il tuo database locale"):
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
        render_page_header("Backup e Ripristino")
        st.caption(f"Cartella backup locale: {os.path.abspath(DEFAULT_BACKUP_DIR)}")

        if st.button("Crea backup ora", type="primary"):
            try:
                backup_path = create_backup()
                st.success(f"Backup creato con successo: {backup_path.name}")
                st.rerun()
            except Exception as exc:
                st.error(f"Errore durante la creazione del backup: {exc}")

        backups = list_backups()

        if backups:
            st.write("Backup salvati in locale")
            df_backups = pd.DataFrame(
                [
                    {
                        "File": b["filename"],
                        "Data e ora": b["created_at"].strftime("%d/%m/%Y %H:%M:%S"),
                        "Dimensione (KB)": b["size_kb"],
                    }
                    for b in backups
                ]
            )
            st.dataframe(df_backups, hide_index=True, width="stretch")

            selected_backup = st.selectbox(
                "Seleziona un backup",
                options=backups,
                format_func=lambda b: f"{b['filename']} ({b['created_at'].strftime('%d/%m/%Y %H:%M:%S')} - {b['size_kb']} KB)",
                key="selected_backup_file",
            )

            if selected_backup:
                backup_bytes = Path(selected_backup["path"]).read_bytes()
                b_col1, b_col2 = st.columns(2)
                with b_col1:
                    st.download_button(
                        label="Scarica backup selezionato",
                        data=backup_bytes,
                        file_name=selected_backup["filename"],
                        mime="application/octet-stream",
                    )
                with b_col2:
                    if st.button("Elimina backup selezionato", type="secondary"):
                        try:
                            if delete_backup(selected_backup["path"]):
                                st.success(f"Backup eliminato: {selected_backup['filename']}")
                                st.rerun()
                            else:
                                st.warning("File di backup non trovato.")
                        except Exception as exc:
                            st.error(f"Errore durante l'eliminazione del backup: {exc}")

                with st.expander("Ripristina dal backup selezionato"):
                    st.warning(
                        "Attenzione: il ripristino sostituisce i dati attuali con quelli del backup scelto. "
                        "Verrà comunque creato automaticamente un backup di sicurezza dei dati attuali."
                    )
                    confirm_local = st.checkbox(
                        "Confermo di voler ripristinare il backup selezionato",
                        key="confirm_restore_local",
                    )
                    if st.button("Ripristina backup selezionato", disabled=not confirm_local):
                        try:
                            safety = restore_backup(selected_backup["path"])
                            init_db()
                            msg = f"Database ripristinato da {selected_backup['filename']}."
                            if safety:
                                msg += f" Backup di sicurezza salvato in: {safety.name}"
                            st.success(msg)
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Errore durante il ripristino: {exc}")
        else:
            st.info("Nessun backup presente. Clicca su 'Crea backup ora' per salvare una copia dei dati.")

        with st.expander("Ripristina da file esterno (.db)"):
            uploaded_file = st.file_uploader("Carica un file di backup SQLite (.db)", type=["db"])
            confirm_upload = st.checkbox(
                "Confermo di voler sovrascrivere i dati attuali con il file caricato",
                key="confirm_restore_upload",
            )
            if st.button(
                    "Ripristina da file caricato",
                    disabled=(uploaded_file is None or not confirm_upload),
            ):
                tmp_path = None
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = Path(tmp.name)

                    safety = restore_backup(tmp_path)
                    init_db()
                    msg = f"Database ripristinato dal file '{uploaded_file.name}'."
                    if safety:
                        msg += f" Backup di sicurezza salvato in: {safety.name}"
                    st.success(msg)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Errore durante il ripristino da file: {exc}")
                finally:
                    if tmp_path and tmp_path.exists():
                        tmp_path.unlink()

with tab_remota:
    st.info("Configura il tuo **supabase remoto** per il tuo gestionale e per l'applicazione per le prenotazioni")

    # ---------------------------------------------------------------------------
    # Possibilità A: Configura Supabase (guida passo passo)
    # ---------------------------------------------------------------------------
    with st.expander("Crea un progetto Supabase"):
        st.markdown("**Passaggio 1 – Creazione account**")
        st.write("Crea un account gratuito su [Supabase](https://supabase.com).")
        st.markdown("**Passaggio 2 – Creazione progetto**")
        st.write("Crea un nuovo progetto Supabase: scegli il nome, la regione e crea la password del database (conservala in un luogo sicuro). Il gestionale non richiede la password del database.")
        st.markdown("**Passaggio 3 – Recupero Project URL**")
        st.write("Nel pannello di controllo di Supabase, clicca sul pulsante **'Connect'**, seleziona **'Connect via API'** e copia il valore del campo **'SUPABASE_URL'** (formato `https://<project-ref>.supabase.co`). Incollalo nel campo dedicato della prossima sezione.")
        st.markdown("**Passaggio 4 – Creazione Personal Access Token**")
        st.write("Genera un PAT in Supabase: vai su Settings → Access Tokens → Generate new token (documentazione: https://supabase.com/docs/guides/platform/access-control). Il token è una credenziale potente: va trattato come una password.")
        st.markdown("**Passaggio 5 – Collegamento**")
        st.write("Inserisci Project URL e PAT, poi premi il pulsante **'Verifica e configura'**.")

    # ---------------------------------------------------------------------------
    # Possibilità B: Ho già un progetto Supabase
    # ---------------------------------------------------------------------------
    with st.expander("Ho già un progetto Supabase"):
        st.caption("Inserisci direttamente i parametri richiesti per il collegamento.")

        project_url = st.text_input("Project URL", placeholder="https://xxxxx.supabase.co")
        pat_token = st.text_input("Personal Access Token (PAT)", type="password", placeholder="Token di accesso...")

        project_ref = extract_project_ref(project_url) if project_url else None
        if project_ref:
            st.caption(f"**Project Reference ID:** {project_ref}")

        if st.button("Verifica e configura", type="primary"):
            if not project_url or not pat_token:
                st.warning("Inserisci sia il Project URL sia il Personal Access Token (PAT) per proseguire.")
            else:
                project_ref = extract_project_ref(project_url)
                if not project_ref:
                    st.error("Impossibile estrarre il Project Reference ID dall'URL. Verifica che l'URL sia corretto.")
                else:
                    try:
                        # Salva il PAT nel Credential Manager (vault sicuro)
                        store_pat(project_ref, pat_token)
                        st.success("PAT salvato in modo sicuro. Avvio procedura di verifica...")
                        st.info(
                            f"Project Reference ID rilevato: {project_ref}. "
                            "Il token è stato memorizzato temporaneamente."
                        )
                    except CredentialStoreUnavailableError:
                        # Se il vault non è disponibile, interrompiamo senza salvare in chiaro
                        st.error(
                            "Impossibile salvare le credenziali: sistema di protezione credenziali non disponibile. "
                            "Immettere i dati di nuovo se si riprova."
                        )
                    except Exception:
                        # Non mostrare mai il token nelle risposte all'utente
                        st.error(
                            "Errore imprevisto durante la gestione delle credenziali. "
                            "Riprova."
                        )
                    else:
                        # Se tutto è andato bene, mostra l'opzione di rimozione
                        if project_ref:
                            confirm_remove = st.checkbox(
                                "Confermo di voler rimuovere le credenziali salvate",
                                key="confirm_remove_pat",
                            )
                            if st.button("Rimuovi credenziali salvate", disabled=not confirm_remove):
                                delete_pat(project_ref)
                                st.success("Credenziali (PAT) cancellate dal vault.")
                                st.rerun()

# st.markdown("---")
render_page_header("Informazioni")
st.write("Private Barber Manager - Versione 1.0 - 26/11/2026")
