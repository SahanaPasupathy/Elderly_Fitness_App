import streamlit as st
from datetime import date
import uuid
import pandas as pd
import sqlite3
from ai_coach_ui import render_ai_coach_ui # <--- MODIFICATION 1: IMPORT ADDED

# --- Database setup ---
conn = sqlite3.connect("elderly_fitness.db", check_same_thread=False)
c = conn.cursor()

# Users table
c.execute("""CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                name TEXT,
                password TEXT,
                role TEXT
            )""")

# Doctor-patient mapping
c.execute("""CREATE TABLE IF NOT EXISTS doctor_patients (
                doctor_email TEXT,
                patient_email TEXT,
                patient_name TEXT,
                PRIMARY KEY (doctor_email, patient_email)
            )""")

# Reminders
c.execute("""CREATE TABLE IF NOT EXISTS reminders (
                reminder_id TEXT PRIMARY KEY,
                doctor_email TEXT,
                patient_email TEXT,
                text TEXT,
                status TEXT
            )""")

# Exercises
c.execute("""CREATE TABLE IF NOT EXISTS exercises (
                id TEXT PRIMARY KEY,
                patient_email TEXT,
                ex_name TEXT,
                ex_date TEXT,
                count INTEGER
            )""")
conn.commit()

# --- Page config ---
st.set_page_config(page_title="Elderly Fitness Tracker", page_icon="❤", layout="wide")


# --- Session state ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_email = ""
    st.session_state.user_name = ""
    st.session_state.patient_feature_page = None
    st.session_state.selected_patient = None
    st.session_state.doctor_page = "dashboard"

# --- Helper functions ---
def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_email = ""
    st.session_state.user_name = ""
    st.session_state.patient_feature_page = None
    st.session_state.selected_patient = None
    st.session_state.doctor_page = "dashboard"
    st.rerun()

def get_user(email):
    c.execute("SELECT name, password, role FROM users WHERE email=?", (email,))
    return c.fetchone()

def create_user(name, email, password, role):
    c.execute("INSERT INTO users (email, name, password, role) VALUES (?, ?, ?, ?)",
              (email, name, password, role))
    conn.commit()

def add_doctor_patient(doctor_email, patient_email, patient_name):
    c.execute("INSERT OR IGNORE INTO doctor_patients (doctor_email, patient_email, patient_name) VALUES (?, ?, ?)",
              (doctor_email, patient_email, patient_name))
    conn.commit()

def get_doctor_patients(doctor_email):
    c.execute("SELECT patient_email, patient_name FROM doctor_patients WHERE doctor_email=?", (doctor_email,))
    return dict(c.fetchall())

def add_reminder(doctor_email, patient_email, text):
    rid = uuid.uuid4().hex
    c.execute("INSERT INTO reminders (reminder_id, doctor_email, patient_email, text, status) VALUES (?, ?, ?, ?, ?)",
              (rid, doctor_email, patient_email, text, "Not Complete"))
    conn.commit()

def get_reminders(doctor_email, patient_email):
    c.execute("SELECT reminder_id, text, status FROM reminders WHERE doctor_email=? AND patient_email=?",
              (doctor_email, patient_email))
    return {rid: {"text": text, "status": status} for rid, text, status in c.fetchall()}

def update_reminder_status(reminder_id, status):
    c.execute("UPDATE reminders SET status=? WHERE reminder_id=?", (status, reminder_id))
    conn.commit()

def delete_reminder(reminder_id):
    c.execute("DELETE FROM reminders WHERE reminder_id=?", (reminder_id,))
    conn.commit()

def add_exercise(patient_email, ex_name, ex_date, count):
    ex_id = uuid.uuid4().hex
    c.execute("INSERT INTO exercises (id, patient_email, ex_name, ex_date, count) VALUES (?, ?, ?, ?, ?)",
              (ex_id, patient_email, ex_name, ex_date, count))
    conn.commit()

def get_exercises(patient_email):
    c.execute("SELECT ex_date, ex_name, count FROM exercises WHERE patient_email=?", (patient_email,))
    data = {}
    for ex_date, ex_name, count in c.fetchall():
        data.setdefault(ex_date, {})
        data[ex_date][ex_name] = count
    return data

def find_doctor(patient_email):
    c.execute("SELECT doctor_email FROM doctor_patients WHERE patient_email=?", (patient_email,))
    res = c.fetchone()
    return res[0] if res else None

# --- Sidebar ---
with st.sidebar:
    st.markdown("## Elderly Fitness Tracker")
    if st.session_state.logged_in:
        welcome_name = st.session_state.user_name
        if st.session_state.role == "doctor":
            st.markdown(f"Welcome, *Dr. {welcome_name}*")
        else:
            st.markdown(f"Welcome, *{welcome_name}*")
        st.markdown(f"Role: {st.session_state.role.capitalize()}")
        if st.button("Logout"):
            logout()
    else:
        st.info("Please sign up or log in to continue.")

# ====================
# Authentication Page
# ====================
if not st.session_state.logged_in:
    st.title("🏥 Elderly Fitness & Health Tracker")
    st.markdown("A simple way for patients and doctors to stay connected on health goals.")
    st.write("")
    
    auth_col1, auth_col2 = st.columns(2)

    with auth_col1:
        with st.container(border=True):
            st.subheader("Create a New Account")
            with st.form("signup_form"):
                su_name = st.text_input("Full Name")
                su_email = st.text_input("Email Address")
                su_password = st.text_input("Password", type="password")
                su_role = st.selectbox("I am a...", ["Patient", "Doctor"])
                
                if st.form_submit_button("Sign Up"):
                    if not su_name or not su_email or not su_password:
                        st.warning("Please fill all fields.")
                    elif get_user(su_email):
                        st.error("This email is already registered.")
                    else:
                        role_db_val = su_role.lower() # Convert to lowercase for db
                        create_user(su_name, su_email, su_password, role_db_val)
                        st.session_state.logged_in = True
                        st.session_state.role = role_db_val
                        st.session_state.user_email = su_email
                        st.session_state.user_name = su_name
                        st.success("Account created successfully!")
                        st.rerun()

    with auth_col2:
        with st.container(border=True):
            st.subheader("Login to Your Account")
            with st.form("login_form"):
                li_email = st.text_input("Email", key="li_email")
                li_password = st.text_input("Password", type="password", key="li_password")
                
                if st.form_submit_button("Login"):
                    user = get_user(li_email)
                    if user:
                        name, password, role = user
                        if li_password == password:
                            st.session_state.logged_in = True
                            st.session_state.role = role
                            st.session_state.user_email = li_email
                            st.session_state.user_name = name
                            st.success("Logged in successfully!")
                            st.rerun()
                        else:
                            st.error("Incorrect password.")
                    else:
                        st.error("Email not found. Please sign up first.")

# ====================
# Doctor Dashboard
# ====================
elif st.session_state.logged_in and st.session_state.role == "doctor":
    st.title(f"👨‍⚕ Doctor Dashboard: Dr. {st.session_state.user_name}")
    doc_patients_page = st.session_state.get("doctor_page", "dashboard")

    if doc_patients_page == "dashboard":
        patients = get_doctor_patients(st.session_state.user_email)
        st.subheader("👥 Your Patients")
        st.metric("Total Patients", len(patients))

        if st.button("➕ Add / Register Patient"):
            st.session_state.doctor_page = "add_patient"
            st.rerun()

        if patients:
            st.subheader("Select Patient to Manage")
            options = ["-- Select a patient --"] + [f"{name} — {email}" for email, name in patients.items()]
            selected = st.selectbox("Pick a patient", options, index=0)
            if selected != "-- Select a patient --":
                selected_email = selected.split("—")[-1].strip()
                st.session_state.selected_patient = selected_email
            else:
                 st.session_state.selected_patient = None


        if st.session_state.selected_patient:
            sp = st.session_state.selected_patient
            patient_name = patients[sp]
            st.markdown(f"### Managing: {patient_name} ({sp})")
            rem_col, ex_col = st.columns(2)

            with rem_col:
                with st.container(border=True):
                    st.markdown("#### Send a Reminder")
                    with st.form(f"send_reminder_form_{sp}"):
                        rem_text = st.text_area("Reminder text", key=f"rem_text_{sp}")
                        if st.form_submit_button("Send Reminder"):
                            if rem_text.strip():
                                add_reminder(st.session_state.user_email, sp, rem_text.strip())
                                st.success("Reminder sent!")
                            else:
                                st.warning("Write a reminder first.")
                    
                    st.markdown("#### Reminders & Status")
                    reminders = get_reminders(st.session_state.user_email, sp)
                    if reminders:
                        for rid, robj in reminders.items():
                            color = "green" if robj["status"] == "Complete" else "grey"
                            st.markdown(f"- {robj['text']} — <span style='color:{color}; font-weight:bold'>{robj['status']}</span>", unsafe_allow_html=True)
                            if st.button("Delete", key=f"delrem_{sp}_{rid}"):
                                delete_reminder(rid)
                                st.rerun()
                    else:
                        st.info("No reminders yet.")
            
            with ex_col:
                with st.container(border=True):
                    st.markdown("#### Log Patient Exercise")
                    with st.form(f"add_exercise_form_{sp}"):
                        ex_date = st.date_input("Date", value=date.today(), key=f"ex_date_{sp}")
                        ex_name = st.text_input("Exercise name", key=f"ex_name_{sp}")
                        ex_count = st.number_input("Count", min_value=0, step=1, key=f"ex_count_{sp}")
                        if st.form_submit_button("Add Exercise"):
                            if not ex_name:
                                st.warning("Provide exercise name.")
                            else:
                                add_exercise(sp, ex_name, ex_date.isoformat(), int(ex_count))
                                st.success("Exercise data added.")

                    st.markdown("#### Exercise History")
                    exercises = get_exercises(sp)
                    if exercises:
                        for dstr, exs in sorted(exercises.items(), reverse=True):
                            st.markdown(f"*Date: {dstr}*")
                            ex_df = pd.DataFrame(list(exs.items()), columns=["Exercise", "Count"])
                            st.table(ex_df.sort_values(by="Count", ascending=False))
                    else:
                        st.info("No exercise data yet.")


    elif doc_patients_page == "add_patient":
        with st.container(border=True):
            st.subheader("➕ Add / Register Patient")
            with st.form("add_patient_form"):
                new_patient_name = st.text_input("Patient Name")
                new_patient_email = st.text_input("Patient Email")
                if st.form_submit_button("Add Patient"):
                    if not new_patient_name or not new_patient_email:
                        st.warning("Provide both name and email.")
                    elif not get_user(new_patient_email):
                        st.error("Patient email not registered. Ask patient to sign up first.")
                    else:
                        add_doctor_patient(st.session_state.user_email, new_patient_email, new_patient_name)
                        st.success(f"Patient {new_patient_name} assigned successfully!")
                        st.session_state.doctor_page = "dashboard"
                        st.rerun()
            if st.button("⬅ Back to Dashboard"):
                st.session_state.doctor_page = "dashboard"
                st.rerun()

# ====================
# Patient Dashboard
# ====================
elif st.session_state.logged_in and st.session_state.role == "patient":
    st.title(f"👵 Patient Dashboard: {st.session_state.user_name}!")
    st.markdown("Here are your tools to stay healthy and connected.")
    st.markdown("---")

    if st.session_state.patient_feature_page is None:
        st.subheader("What would you like to do today?")
        
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.markdown("#### ✅ My Reminders")
                st.markdown("View and check off tasks from your doctor.")
                if st.button("Open Reminders", key="reminders_btn", use_container_width=True):
                    st.session_state.patient_feature_page = "tick_reminders"
                    st.rerun()
            
            with st.container(border=True):
                st.markdown("#### 📊 My Exercise History")
                st.markdown("See a log of all your completed exercises.")
                if st.button("View History", key="history_btn", use_container_width=True):
                    st.session_state.patient_feature_page = "exercise_count"
                    st.rerun()
        
        with col2:
            with st.container(border=True):
                st.markdown("#### 📞 My Doctor's Contact")
                st.markdown("Easily find your doctor's contact details.")
                if st.button("See Contact Info", key="contact_btn", use_container_width=True):
                    st.session_state.patient_feature_page = "doctor_contact"
                    st.rerun()

            with st.container(border=True):
                st.markdown("#### 🏋 Fitness Tracker")
                st.markdown("Access your AI-powered personal trainer.")
                if st.button("Open Tracker", key="tracker_btn", use_container_width=True):
                    st.session_state.patient_feature_page = "fitness_tracker"
                    st.rerun()

    elif st.session_state.patient_feature_page == "tick_reminders":
        st.subheader("✅ Reminders from Your Doctor")
        doctor_email = find_doctor(st.session_state.user_email)

        def reminder_status_changed(reminder_id):
            new_status_bool = st.session_state[f"patrem_{reminder_id}"]
            update_reminder_status(reminder_id, "Complete" if new_status_bool else "Not Complete")

        if doctor_email:
            reminders = get_reminders(doctor_email, st.session_state.user_email)
            if reminders:
                st.info("Check the box next to a reminder once you have completed it.")
                for rid, r in reminders.items():
                    checked = r["status"] == "Complete"
                    st.checkbox(r["text"], value=checked, key=f"patrem_{rid}", on_change=reminder_status_changed, args=(rid,))
            else:
                st.success("You have no reminders from your doctor. All caught up!")
        else:
            st.warning("You are not yet assigned to a doctor.")

        if st.button("⬅ Back to Main Menu"):
            st.session_state.patient_feature_page = None
            st.rerun()

    # <--- MODIFICATION 2: THIS ENTIRE BLOCK IS REPLACED ---
    elif st.session_state.patient_feature_page == "fitness_tracker":
        st.subheader("🏋 Fitness Tracker Module")
        
        # This function call renders the entire AI coach interface
        render_ai_coach_ui()
        
        if st.button("⬅ Back to Main Menu"):
            st.session_state.patient_feature_page = None
            # Clear any lingering session state from the AI coach
            if 'final_count' in st.session_state:
                del st.session_state.final_count
            if 'exercise_name' in st.session_state:
                del st.session_state.exercise_name
            st.rerun()
    # <--- END OF MODIFICATION ---

    elif st.session_state.patient_feature_page == "exercise_count":
        st.subheader("📊 My Exercise History")
        exercises = get_exercises(st.session_state.user_email)
        if exercises:
            all_data = []
            for dstr, exs in exercises.items():
                for ex, cnt in exs.items():
                    all_data.append({"Date": dstr, "Exercise": ex, "Count": cnt})
            df_all = pd.DataFrame(all_data)
            st.dataframe(df_all.sort_values(by=["Date", "Count"], ascending=[False, False]))
        else:
            st.info("No exercise data has been recorded yet.")
        if st.button("⬅ Back to Main Menu"):
            st.session_state.patient_feature_page = None
            st.rerun()

    elif st.session_state.patient_feature_page == "doctor_contact":
        st.subheader("📞 My Doctor's Contact Details")
        doctor_email = find_doctor(st.session_state.user_email)
        if doctor_email:
            doc_info = get_user(doctor_email)
            st.markdown(f"*Doctor Name:* Dr. {doc_info[0]}")
            st.markdown(f"*Email:* {doctor_email}")
        else:
            st.warning("You are not yet assigned to a doctor.")

        if st.button("⬅ Back to Main Menu"):
            st.session_state.patient_feature_page = None
            st.rerun()

# --- Footer ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: grey;'>Elderly Fitness Tracker Demo</div>", unsafe_allow_html=True)