import streamlit as st
import cv2
import tempfile
import ExerciseAiTrainer as exercise
from chatbot import chat_ui
from datetime import date
import time

def render_ai_coach_ui():
    """
    This function renders the AI Coach UI and handles its internal navigation.
    """
    # Initialize internal state for the AI Coach module
    if "coach_page" not in st.session_state:
        st.session_state.coach_page = "menu"

    # Helper function to add exercise data to the database
    def add_exercise_to_db(patient_email, ex_name, ex_date, count):
        import sqlite3, uuid
        conn = sqlite3.connect("elderly_fitness.db")
        c = conn.cursor()
        ex_id = uuid.uuid4().hex
        c.execute("INSERT INTO exercises (id, patient_email, ex_name, ex_date, count) VALUES (?, ?, ?, ?, ?)",
                  (ex_id, patient_email, ex_name, ex_date, count))
        conn.commit()
        conn.close()

    # --- Main Menu for the AI Coach ---
    if st.session_state.coach_page == "menu":
        st.title("Fitness AI Coach")
        st.markdown("Choose an option to begin your session.")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💪 Live Webcam Session", use_container_width=True):
                st.session_state.coach_page = "webcam"
                st.rerun()
        with col2:
            if st.button("📹 Upload Video", use_container_width=True):
                st.session_state.coach_page = "video"
                st.rerun()
        with col3:
            if st.button("🤖 Fitness Chatbot", use_container_width=True):
                st.session_state.coach_page = "chatbot"
                st.rerun()

    # --- Live Webcam Page ---
    elif st.session_state.coach_page == "webcam":
        st.subheader("Live Webcam Session")
        if st.button("⬅️ Back to Coach Menu"):
            st.session_state.coach_page = "menu"
            st.rerun()
        
        exercise_options = st.selectbox('Select Exercise', ('Push Up', 'Squat', 'Shoulder Press'), key="webcam_ex")
        if st.button('Start Exercise'):
            exer = exercise.Exercise()
            cap = cv2.VideoCapture(0)
            final_count = 0
            if exercise_options == 'Push Up': final_count = exer.push_up(cap)
            elif exercise_options == 'Squat': final_count = exer.squat(cap)
            elif exercise_options == 'Shoulder Press': final_count = exer.shoulder_press(cap)
            
            st.session_state.final_count = final_count
            st.session_state.exercise_name = exercise_options
            st.rerun()

    # --- Upload Video Page ---
    elif st.session_state.coach_page == "video":
        st.subheader("Upload Video Analysis")
        if st.button("⬅️ Back to Coach Menu"):
            st.session_state.coach_page = "menu"
            st.rerun()
        
        st.write('## Upload your video to count repetitions')
        exercise_options = st.selectbox(
            'Select Exercise', ('Push Up', 'Squat', 'Shoulder Press'), key="video_ex"
        )
        video_file_buffer = st.file_uploader("Upload a video", type=["mp4", "mov", 'avi'])

        if video_file_buffer is not None:
            tfflie = tempfile.NamedTemporaryFile(delete=False)
            tfflie.write(video_file_buffer.read())
            
            if st.button("Analyze Video"):
                cap = cv2.VideoCapture(tfflie.name)
                st.info("Analyzing video... Please wait.")
                exer = exercise.Exercise()
                final_count = 0
                if exercise_options == 'Push Up':
                    final_count = exer.push_up(cap, is_video=True)
                elif exercise_options == 'Squat':
                    final_count = exer.squat(cap, is_video=True)
                elif exercise_options == 'Shoulder Press':
                    final_count = exer.shoulder_press(cap, is_video=True)

                st.session_state.final_count = final_count
                st.session_state.exercise_name = exercise_options
                st.rerun()

    # --- Chatbot Page ---
    elif st.session_state.coach_page == "chatbot":
        st.subheader("Fitness Chatbot")
        if st.button("⬅️ Back to Coach Menu"):
            st.session_state.coach_page = "menu"
            st.rerun()
        chat_ui()

    # --- SAVE EXERCISE FORM (appears after a session) ---
    if 'final_count' in st.session_state and 'exercise_name' in st.session_state:
        final_count = st.session_state.get('final_count', 0)
        exercise_name = st.session_state.get('exercise_name', 'Unknown Exercise')
        
        if final_count > 0:
            st.success(f"Session Complete! You did {final_count} reps of {exercise_name}.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Exercise to My History", use_container_width=True):
                    add_exercise_to_db(st.session_state.user_email, exercise_name, date.today().isoformat(), final_count)
                    st.success("Successfully saved!")
                    del st.session_state['final_count']
                    del st.session_state['exercise_name']
                    time.sleep(1)
                    st.rerun()
            
            with col2:
                if st.button("⬅️ Try Another Exercise", use_container_width=True):
                    # Clear the results from the last session
                    del st.session_state['final_count']
                    del st.session_state['exercise_name']
                    # Go back to the coach menu
                    st.session_state.coach_page = "menu"
                    st.rerun()

