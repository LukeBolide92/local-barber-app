import streamlit as st
import pandas as pd
from datetime import date, time, datetime, timedelta
import calendar

st.title("Appuntamenti")

# Init session_state demo data with relative dates
if "appointments_data" not in st.session_state:
    today = date.today()
    st.session_state.appointments_data = [
        {"id": 1, "date": today, "client": "Mario Rossi", "service": "Taglio + Barba", "collaborator": "Marco", "time": "09:00"},
        {"id": 2, "date": today, "client": "Luca Verdi", "service": "Taglio", "collaborator": "Paolo", "time": "10:30"},
        {"id": 3, "date": today + timedelta(days=1), "client": "Giulia Bianchi", "service": "Colorazione", "collaborator": "Marco", "time": "14:00"},
        {"id": 4, "date": today + timedelta(days=2), "client": "Mario Rossi", "service": "Barba", "collaborator": "Paolo", "time": "15:30"},
        {"id": 5, "date": today + timedelta(days=2), "client": "Giulia Bianchi", "service": "Taglio", "collaborator": "Marco", "time": "16:30"},
    ]
    st.session_state.next_appt_id = 6

all_appointments = st.session_state.appointments_data

clients = [
    {"id": 1, "name": "Mario Rossi"},
    {"id": 2, "name": "Luca Verdi"},
    {"id": 3, "name": "Giulia Bianchi"},
]
services = [
    {"id": 1, "name": "Taglio", "duration": 30, "price": 18.0},
    {"id": 2, "name": "Barba", "duration": 20, "price": 12.0},
    {"id": 3, "name": "Taglio + Barba", "duration": 45, "price": 25.0},
    {"id": 4, "name": "Colorazione", "duration": 60, "price": 55.0},
]
collaborators = [
    {"id": 1, "name": "Marco"},
    {"id": 2, "name": "Paolo"},
]

tab_list, tab_cal, tab_new = st.tabs(["Elenco", "Calendario", "Nuovo appuntamento"])

with tab_list:
    st.subheader("Filtri")
    col1, col2 = st.columns(2)
    with col1:
        filter_date = st.date_input("Data", value=date.today())
    with col2:
        filter_collab = st.selectbox("Collaboratore", ["Tutti"] + [c["name"] for c in collaborators])

    filtered = [a for a in all_appointments if a["date"] == filter_date]
    if filter_collab != "Tutti":
        filtered = [a for a in filtered if a["collaborator"] == filter_collab]

    if filtered:
        df = pd.DataFrame(filtered)
        df = df.rename(columns={
            "id": "ID",
            "date": "Data",
            "client": "Cliente",
            "service": "Servizio",
            "collaborator": "Collaboratore",
            "time": "Orario",
        })
        st.dataframe(df, hide_index=True)
    else:
        st.info("Nessun appuntamento per i filtri selezionati.")

with tab_cal:
    st.subheader("Calendario")
    col1, col2 = st.columns(2)
    with col1:
        cal_start = st.date_input("Data inizio", value=date.today())
    with col2:
        cal_week_mode = st.checkbox("Vista settimanale", value=True)

    # Determine date range
    if cal_week_mode:
        # Monday-based week
        monday = cal_start - timedelta(days=cal_start.weekday())
        week_dates = [monday + timedelta(days=i) for i in range(7)]
        display_dates = week_dates
    else:
        display_dates = [cal_start]

    # Build a grid: rows = time slots (09-18), cols = dates
    time_slots = [f"{h:02d}:00" for h in range(9, 19)]
    cal_data = {slot: [] for slot in time_slots}
    for d in display_dates:
        cal_data[d] = {slot: [] for slot in time_slots}

    for a in all_appointments:
        for d in display_dates:
            if a["date"] == d:
                # Map time to nearest slot
                hhmm = a["time"]
                slot = hhmm[:2] + ":00"
                if slot in cal_data[d]:
                    cal_data[d][slot].append(a)

    if cal_week_mode:
        # Build table for week view
        week_rows = []
        for slot in time_slots:
            row = {"Orario": slot}
            for d in display_dates:
                apps = cal_data[d].get(slot, [])
                if apps:
                    row[str(d)] = "\n".join(
                        f"{a['client']} ({a['service']}) - {a['collaborator']}" for a in apps
                    )
                else:
                    row[str(d)] = ""
            week_rows.append(row)
        if week_rows:
            df_cal = pd.DataFrame(week_rows)
            df_cal = df_cal.set_index("Orario")
            st.dataframe(df_cal, use_container_width=True)
        else:
            st.info("Nessun appuntamento nella settimana selezionata.")
    else:
        # Single day view: columns = collaborators
        day = cal_start
        collab_names = [c["name"] for c in collaborators]
        day_rows = []
        for slot in time_slots:
            row = {"Orario": slot}
            for cname in collab_names:
                apps = [
                    a for a in all_appointments
                    if a["date"] == day and a["collaborator"] == cname
                    and a["time"][:2] + ":00" == slot
                ]
                if apps:
                    row[cname] = "\n".join(
                        f"{a['client']} ({a['service']})" for a in apps
                    )
                else:
                    row[cname] = ""
            day_rows.append(row)
        df_day = pd.DataFrame(day_rows).set_index("Orario")
        st.dataframe(df_day, use_container_width=True)

with tab_new:
    st.subheader("Nuovo appuntamento")
    with st.form("new_appointment_form"):
        client = st.selectbox("Cliente", [c["name"] for c in clients])
        service = st.selectbox("Servizio", [s["name"] for s in services])
        collaborator = st.selectbox("Collaboratore", [c["name"] for c in collaborators])
        appt_date = st.date_input("Data", value=date.today())
        appt_time = st.time_input("Orario", value=time(9, 0))
        notes = st.text_area("Note", height=80)
        submitted = st.form_submit_button("Salva")
        if submitted:
            st.session_state.appointments_data.append({
                "id": st.session_state.next_appt_id,
                "date": appt_date,
                "client": client,
                "service": service,
                "collaborator": collaborator,
                "time": appt_time.strftime("%H:%M"),
                "notes": notes,
            })
            st.session_state.next_appt_id += 1
            st.success("Appuntamento creato (demo).")
            st.rerun()