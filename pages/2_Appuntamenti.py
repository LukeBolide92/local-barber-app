from datetime import date, time, timedelta
import pandas as pd
import streamlit as st
from database import get_session, init_db
from services.appointment_service import (
    create_appointment,
    delete_appointment,
    get_appointments,
    get_appointments_in_range,
    is_collaborator_available,
    check_appointment_conflict,
    update_appointment,
    cancel_appointment,
    register_no_show,
)
from services.payment_service import (
    register_payment,
    register_refund,
    get_payment_details,
    complete_appointment_and_register_quick_payment,
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

STATUS_LABELS = {
    "BOOKED": "Prenotato",
    "COMPLETED": "Completato",
    "CANCELLED": "Annullato",
    "NO_SHOW": "Assente",
}

with tab_list:
    st.subheader("Filtri")
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
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
        status_options = [("Tutti", None)] + [(label, key) for key, label in STATUS_LABELS.items()]
        selected_status = st.selectbox(
            "Stato",
            options=status_options,
            format_func=lambda item: item[0],
            key="appt_list_status",
        )
    with col4:
        show_all_dates = st.checkbox("Tutte le date", value=False, key="appt_list_all")

    try:
        with get_session() as session:
            filtered = get_appointments(
                session,
                date_filter=None if show_all_dates else filter_date,
                collaborator_id=selected_collab[1],
                status_filter=selected_status[1],
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
                "Prezzo": float(a.price) if a.price is not None else (
                    float(a.service.price) if a.service else 0.0
                ),
                "Stato": STATUS_LABELS.get(a.status, a.status),
                "Pagamento": a.payment_status or "UNPAID",
                "Importo pagato": float(a.amount_paid) if a.amount_paid is not None else 0.0,
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

        with st.expander("Gestisci appuntamento"):
            appt_selected = st.selectbox(
                "Seleziona appuntamento",
                options=filtered,
                format_func=lambda a: (
                    f"#{a.id} - {a.date} {a.time.strftime('%H:%M')} - "
                    f"{a.client.name if a.client else '-'} ({a.service.name if a.service else '-'}) "
                    f"[{STATUS_LABELS.get(a.status, a.status)}]"
                ),
                key="manage_appt_select",
            )
            st.caption(f"Stato attuale: {STATUS_LABELS.get(appt_selected.status, appt_selected.status)}")

            act_col1, act_col2, act_col3 = st.columns(3)
            with act_col1:
                default_amount = float(appt_selected.price) if appt_selected.price is not None else (
                    float(appt_selected.service.price) if appt_selected.service else 0.0
                )
                with st.form(f"complete_payment_form_{appt_selected.id}"):
                    paid_amount = st.number_input(
                        "Importo pagato (€)",
                        min_value=0.0,
                        max_value=max(default_amount, 0.0),
                        value=default_amount,
                        step=0.5,
                        key=f"pay_amount_{appt_selected.id}",
                    )
                    pay_method = st.selectbox(
                        "Metodo di pagamento",
                        options=["Contanti", "Carta", "Bonifico", "Altro"],
                        index=["Contanti", "Carta", "Bonifico", "Altro"].index(
                            appt_selected.payment_method or "Contanti"
                        ) if appt_selected.payment_method else 0,
                        key=f"pay_method_{appt_selected.id}",
                    )
                    submit_complete = st.form_submit_button(
                        "Completa e conferma pagamento",
                        disabled=appt_selected.status in ("CANCELLED", "NO_SHOW") or appt_selected.status == "COMPLETED",
                    )
                    if submit_complete:
                        try:
                            with get_session() as session:
                                result = complete_appointment_and_register_quick_payment(
                                    session,
                                    appt_selected.id,
                                    amount=float(paid_amount) if paid_amount > 0 else default_amount,
                                    method=pay_method,
                                )
                            if result:
                                st.success("Appuntamento completato e pagamento confermato.")
                                st.rerun()
                            else:
                                st.warning("Impossibile completare l'appuntamento.")
                        except Exception as exc:
                            st.error(f"Errore: {exc}")
            with act_col2:
                if st.button("Annulla", key="btn_cancel", disabled=appt_selected.status in ("COMPLETED", "NO_SHOW")):
                    try:
                        with get_session() as session:
                            ok = cancel_appointment(session, appt_selected.id)
                        if ok:
                            st.success("Appuntamento annullato.")
                            st.rerun()
                        else:
                            st.warning("Impossibile annullare l'appuntamento.")
                    except Exception as exc:
                        st.error(f"Errore: {exc}")
            with act_col3:
                if st.button("Registra assente", key="btn_no_show", disabled=appt_selected.status in ("COMPLETED", "CANCELLED")):
                    try:
                        with get_session() as session:
                            ok = register_no_show(session, appt_selected.id)
                        if ok:
                            st.success("Assenza registrata.")
                            st.rerun()
                        else:
                            st.warning("Impossibile registrare l'assenza.")
                    except Exception as exc:
                        st.error(f"Errore: {exc}")

            st.markdown("**Modifica appuntamento**")
            with st.form(f"edit_appt_form_{appt_selected.id}"):
                new_date = st.date_input("Nuova data", value=appt_selected.date, key="edit_date")
                new_time = st.time_input("Nuovo orario", value=appt_selected.time, key="edit_time")
                new_notes = st.text_area("Note", value=appt_selected.notes or "", key="edit_notes", height=70)
                new_status = st.selectbox(
                    "Stato",
                    options=list(STATUS_LABELS.keys()),
                    index=list(STATUS_LABELS.keys()).index(appt_selected.status),
                    format_func=lambda k: STATUS_LABELS[k],
                    key="edit_status",
                )
                save_edit = st.form_submit_button("Salva modifiche")
                if save_edit:
                    try:
                        with get_session() as session:
                            updated = update_appointment(
                                session,
                                appt_selected.id,
                                date=new_date,
                                time=new_time,
                                notes=new_notes.strip() or None,
                                status=new_status,
                            )
                        if updated:
                            st.success("Appuntamento aggiornato.")
                            st.rerun()
                        else:
                            st.warning("Appuntamento non trovato.")
                    except Exception as exc:
                        st.error(f"Errore durante la modifica: {exc}")

            st.markdown("**Gestione pagamenti**")
            current_payment = None
            try:
                with get_session() as session:
                    current_payment = get_payment_details(session, appt_selected.id)
            except Exception as exc:
                st.error(f"Errore nel caricamento del pagamento: {exc}")
                current_payment = None

            pay_col1, pay_col2, pay_col3 = st.columns(3)
            with pay_col1:
                if st.button("Registra pagamento", key="btn_reg_payment", disabled=(appt_selected.status != "COMPLETED")):
                    try:
                        with get_session() as session:
                            result = register_payment(
                                session,
                                appt_selected.id,
                                amount=float(appt_selected.price or (appt_selected.service.price if appt_selected.service else 0.0)),
                                method="Contanti",
                            )
                        if result:
                            st.success("Pagamento registrato.")
                            st.rerun()
                        else:
                            st.warning("Impossibile registrare il pagamento.")
                    except Exception as exc:
                        st.error(f"Errore: {exc}")
            with pay_col2:
                if st.button("Rendi rimborso", key="btn_reg_refund", disabled=(appt_selected.status != "COMPLETED" or current_payment is None or current_payment.get("payment_status") == "REFUNDED")):
                    try:
                        with get_session() as session:
                            result = register_refund(session, appt_selected.id)
                        if result:
                            st.success("Rimborso registrato.")
                            st.rerun()
                        else:
                            st.warning("Impossibile registrare il rimborso.")
                    except Exception as exc:
                        st.error(f"Errore: {exc}")
            with pay_col3:
                if current_payment:
                    st.write(f"Stato pagamento: **{current_payment.get('payment_status')}**")
                    st.write(f"Importo pagato: **€ {float(current_payment.get('amount_paid') or 0):.2f}**")
                    st.write(f"Metodo: **{current_payment.get('payment_method')}**")
                    if current_payment.get("payment_datetime"):
                        st.write(f"Data/Ora: **{current_payment.get('payment_datetime')}**")

            st.markdown("---")
            if st.button("Elimina definitivamente", type="secondary", key="btn_delete"):
                try:
                    with get_session() as session:
                        deleted = delete_appointment(session, appt_selected.id)
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
                except ValueError as ve:
                    st.error(f"Errore di validazione: {ve}")
                except Exception as exc:
                    st.error(f"Errore durante il salvataggio dell'appuntamento: {exc}")
