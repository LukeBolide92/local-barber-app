from datetime import date, time, timedelta
import pandas as pd
import streamlit as st
from database import get_session, init_db
from services.appointment_service import (
    create_appointment,
    delete_appointment,
    get_appointments,
    get_appointments_in_range,
)
from services.client_service import get_clients
from services.collaborator_service import get_collaborators
from services.service import get_services

init_db()

st.title("Appuntamenti")

try:
    with get_session() as session:
        clients = get_clients(session)
        services = get_services(session)
        collaborators = get_collaborators(session)
except Exception as exc:
    st.error(f"Errore nel caricamento dei dati di base: {exc}")
    st.stop()

tab_list, tab_cal, tab_new = st.tabs(["Elenco", "Calendario", "Nuovo appuntamento"])

with tab_list:
    st.subheader("Filtri")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        filter_date = st.date_input("Data", value=date.today(), key="appt_list_date")
    with col2:
        collab_options = [("Tutti", None)] + [(c.name, c.id) for c in collaborators]
        selected_collab = st.selectbox(
            "Collaboratore",
            options=collab_options,
            format_func=lambda item: item[0],
            key="appt_list_collab",
        )
    with col3:
        show_all_dates = st.checkbox("Tutte le date", value=False, key="appt_list_all")

    try:
        with get_session() as session:
            filtered = get_appointments(
                session,
                date_filter=None if show_all_dates else filter_date,
                collaborator_id=selected_collab[1],
            )
    except Exception as exc:
        st.error(f"Errore nel recupero degli appuntamenti: {exc}")
        filtered = []

    if filtered:
        rows = [
            {
                "ID": a.id,
                "Data": a.date,
                "Orario": a.time.strftime("%H:%M"),
                "Cliente": a.client.name if a.client else "-",
                "Servizio": a.service.name if a.service else "-",
                "Collaboratore": a.collaborator.name if a.collaborator else "-",
                "Prezzo": float(a.service.price) if a.service else 0.0,
                "Note": a.notes or "",
            }
            for a in filtered
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

        with st.expander("Elimina appuntamento"):
            appt_to_delete = st.selectbox(
                "Seleziona appuntamento da eliminare",
                options=filtered,
                format_func=lambda a: (
                    f"#{a.id} - {a.date} {a.time.strftime('%H:%M')} - "
                    f"{a.client.name if a.client else '-'} ({a.service.name if a.service else '-'})"
                ),
                key="delete_appt_select",
            )
            if st.button("Elimina appuntamento", type="secondary"):
                try:
                    with get_session() as session:
                        deleted = delete_appointment(session, appt_to_delete.id)
                    if deleted:
                        st.success("Appuntamento eliminato.")
                        st.rerun()
                    else:
                        st.warning("Appuntamento non trovato.")
                except Exception as exc:
                    st.error(f"Errore durante l'eliminazione: {exc}")
    else:
        st.info("Nessun appuntamento per i filtri selezionati.")

with tab_cal:
    st.subheader("Calendario")
    col1, col2 = st.columns(2)
    with col1:
        cal_start = st.date_input("Data di riferimento", value=date.today(), key="appt_cal_date")
    with col2:
        cal_week_mode = st.checkbox("Vista settimanale", value=True, key="appt_cal_week")

    if cal_week_mode:
        monday = cal_start - timedelta(days=cal_start.weekday())
        display_dates = [monday + timedelta(days=i) for i in range(7)]
        range_start, range_end = display_dates[0], display_dates[-1]
    else:
        display_dates = [cal_start]
        range_start = range_end = cal_start

    try:
        with get_session() as session:
            range_appointments = get_appointments_in_range(session, range_start, range_end)
    except Exception as exc:
        st.error(f"Errore nel caricamento del calendario: {exc}")
        range_appointments = []

    time_slots = [f"{h:02d}:00" for h in range(8, 21)]

    if cal_week_mode:
        cal_data = {d: {slot: [] for slot in time_slots} for d in display_dates}
        for a in range_appointments:
            slot = f"{a.time.hour:02d}:00"
            if a.date in cal_data and slot in cal_data[a.date]:
                cal_data[a.date][slot].append(a)

        week_rows = []
        for slot in time_slots:
            row = {"Orario": slot}
            for d in display_dates:
                apps = cal_data[d][slot]
                row[d.strftime("%d/%m")] = (
                    "\n".join(
                        f"{a.time.strftime('%H:%M')} {a.client.name if a.client else '-'} "
                        f"({a.service.name if a.service else '-'}) - "
                        f"{a.collaborator.name if a.collaborator else '-'}"
                        for a in apps
                    )
                    if apps
                    else ""
                )
            week_rows.append(row)

        df_cal = pd.DataFrame(week_rows).set_index("Orario")
        st.dataframe(df_cal, width="stretch")
    else:
        collab_names = [c.name for c in collaborators]
        if not collab_names:
            st.info("Nessun collaboratore configurato.")
        else:
            day_rows = []
            for slot in time_slots:
                row = {"Orario": slot}
                for cname in collab_names:
                    apps = [
                        a
                        for a in range_appointments
                        if a.date == cal_start
                        and a.collaborator
                        and a.collaborator.name == cname
                        and f"{a.time.hour:02d}:00" == slot
                    ]
                    row[cname] = (
                        "\n".join(
                            f"{a.time.strftime('%H:%M')} {a.client.name if a.client else '-'} "
                            f"({a.service.name if a.service else '-'})"
                            for a in apps
                        )
                        if apps
                        else ""
                    )
                day_rows.append(row)
            df_day = pd.DataFrame(day_rows).set_index("Orario")
            st.dataframe(df_day, width="stretch")

with tab_new:
    st.subheader("Nuovo appuntamento")
    available_collaborators = [c for c in collaborators if c.availability == 1]

    if not clients or not services or not available_collaborators:
        missing = []
        if not clients:
            missing.append("almeno un cliente")
        if not services:
            missing.append("almeno un servizio")
        if not available_collaborators:
            missing.append("almeno un collaboratore disponibile")
        st.warning(f"Per creare un appuntamento devi prima inserire: {', '.join(missing)}.")
    else:
        with st.form("new_appointment_form"):
            selected_client = st.selectbox(
                "Cliente",
                options=clients,
                format_func=lambda c: f"{c.name} ({c.phone})",
            )
            selected_service = st.selectbox(
                "Servizio",
                options=services,
                format_func=lambda s: f"{s.name} - {s.duration_minutes} min (€ {s.price:.2f})",
            )
            selected_collaborator = st.selectbox(
                "Collaboratore",
                options=available_collaborators,
                format_func=lambda col: f"{col.name} ({col.role})",
            )
            appt_date = st.date_input("Data", value=date.today())
            appt_time = st.time_input("Orario", value=time(9, 0))
            notes = st.text_area("Note", height=80)
            submitted = st.form_submit_button("Salva")

            if submitted:
                try:
                    with get_session() as session:
                        create_appointment(
                            session,
                            client_id=selected_client.id,
                            service_id=selected_service.id,
                            collaborator_id=selected_collaborator.id,
                            appt_date=appt_date,
                            appt_time=appt_time,
                            notes=notes.strip() if notes.strip() else None,
                        )
                    st.success("Appuntamento salvato nel database.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Errore durante il salvataggio dell'appuntamento: {exc}")
