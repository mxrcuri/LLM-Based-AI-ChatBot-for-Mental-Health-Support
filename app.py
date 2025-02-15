# app.py
import streamlit as st
import sqlite3
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import hashlib
import time
from datetime import datetime

# --------------------------
# Page Configuration (MUST BE FIRST)
# --------------------------
st.set_page_config(
    page_title="MindMate AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --------------------------
# Custom CSS Styling
# --------------------------
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .header {
        padding: 2rem 1rem;
        background-color: #ffffff;
        border-bottom: 1px solid #e9ecef;
    }
    .chat-container {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        padding: 1.5rem;
        margin-top: 1rem;
    }
    .user-message {
        background-color: #007bff;
        color: white;
        border-radius: 15px;
        padding: 0.8rem 1.2rem;
        margin: 0.5rem 0;
        max-width: 80%;
        float: right;
    }
    .bot-message {
        background-color: #e9ecef;
        color: black;
        border-radius: 15px;
        padding: 0.8rem 1.2rem;
        margin: 0.5rem 0;
        max-width: 80%;
    }
    .tab-content {
        padding: 1rem;
        border-radius: 8px;
        background-color: white;
        margin-top: 1rem;
    }
    .session-card {
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.2s ease;
    }
    .session-card:hover {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------
# Database Setup
# --------------------------
def init_db():
    conn = sqlite3.connect('mental_health.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password_hash TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  session_type TEXT,
                  session_topic TEXT,
                  start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  end_time TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id INTEGER,
                  content TEXT,
                  is_user BOOLEAN,
                  sentiment_score REAL,
                  detected_emotion TEXT,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(session_id) REFERENCES sessions(id))''')
    
    conn.commit()
    conn.close()

init_db()

# --------------------------
# Authentication System
# --------------------------
def create_user(username, password):
    conn = sqlite3.connect('mental_health.db')
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
              (username, hashed_pw))
    conn.commit()
    conn.close()

def authenticate(username, password):
    conn = sqlite3.connect('mental_health.db')
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT id FROM users WHERE username=? AND password_hash=?", 
              (username, hashed_pw))
    user_id = c.fetchone()
    conn.close()
    return user_id[0] if user_id else None

# --------------------------
# AI Configuration
# --------------------------
def init_gemini():
    return ChatGoogleGenerativeAI(
        model="gemini-pro",
        temperature=0.7,
        google_api_key=st.secrets["GOOGLE_API_KEY"]
    )

# --------------------------
# Emotion Analysis Chain
# --------------------------
emotion_chain = (
    ChatPromptTemplate.from_template(
        "Analyze the emotion in this message on scale 1-10 "
        "(1=negative, 10=positive). "
        "Format: score|emotion|short_reason. Message: {message}"
    )
    | init_gemini()
    | StrOutputParser()
)

# --------------------------
# Session Management
# --------------------------
def create_session(user_id, session_type, topic=None):
    conn = sqlite3.connect('mental_health.db')
    c = conn.cursor()
    c.execute("INSERT INTO sessions (user_id, session_type, session_topic) VALUES (?, ?, ?)",
              (user_id, session_type, topic))
    session_id = c.lastrowid
    conn.commit()
    conn.close()
    return session_id

def end_session(session_id):
    conn = sqlite3.connect('mental_health.db')
    c = conn.cursor()
    c.execute("UPDATE sessions SET end_time = CURRENT_TIMESTAMP WHERE id = ?",
              (session_id,))
    conn.commit()
    conn.close()

# --------------------------
# Response Generation Chains
# --------------------------
def get_response_chain(session_type, topic=None):
    if session_type == "diagnosis":
        prompt = ChatPromptTemplate.from_template("""
        As a mental health diagnosis assistant, analyze these symptoms: {message}
        Consider possible conditions, severity (mild/moderate/severe), 
        and recommend next steps. Be compassionate but factual.
        """)
    elif session_type == "topic":
        prompt = ChatPromptTemplate.from_template("""
        You're a {topic} specialist counselor. Respond to: {message}
        Use evidence-based techniques (CBT, DBT). 
        Keep responses conversational and supportive.
        """)
    else:
        prompt = ChatPromptTemplate.from_template("""
        You're a compassionate mental health companion. Respond to: {message}
        Use active listening and positive reinforcement. 
        Keep responses under 100 words.
        """)
    
    return prompt | init_gemini() | StrOutputParser()

# --------------------------
# Chat History Functions
# --------------------------
def get_chat_history(user_id):
    conn = sqlite3.connect('mental_health.db')
    c = conn.cursor()
    c.execute('''SELECT s.id, s.session_type, s.session_topic, s.start_time, 
                 GROUP_CONCAT(m.content, '|||') as messages
                 FROM sessions s
                 LEFT JOIN messages m ON s.id = m.session_id
                 WHERE s.user_id = ?
                 GROUP BY s.id
                 ORDER BY s.start_time DESC''', (user_id,))
    history = c.fetchall()
    conn.close()
    return history

# --------------------------
# Main Application
# --------------------------
def main():
    # Initialize session state
    session_defaults = {
        'user_id': None,
        'session_id': None,
        'current_session_type': 'general',
        'current_topic': None,
        'messages': [],
        'active_tab': 'General'
    }
    
    for key, value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Authentication Flow
    if not st.session_state.user_id:
        with st.container():
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                st.markdown("<div class='header'><h1 style='text-align: center'>🧠 MindMate AI</h1></div>", unsafe_allow_html=True)
                auth_choice = st.radio("Choose Action", ["Login", "Register"], horizontal=True)
                username = st.text_input("Username")
                
                if auth_choice == "Register":
                    password = st.text_input("Password", type="password", key="pass1")
                    confirm_password = st.text_input("Confirm Password", type="password", key="pass2")
                else:
                    password = st.text_input("Password", type="password")
                
                if st.button("Continue", use_container_width=True):
                    if auth_choice == "Register":
                        if password != confirm_password:
                            st.error("Passwords do not match!")
                            return
                        create_user(username, password)
                        st.success("Account created! Please login.")
                    else:
                        user_id = authenticate(username, password)
                        if user_id:
                            st.session_state.user_id = user_id
                            st.rerun()
                        else:
                            st.error("Invalid credentials")
                st.markdown("---")
                st.markdown("<div style='text-align: center; color: #6c757d'>Your mental health matters. Talk to our AI companion anytime.</div>", unsafe_allow_html=True)
        return

    # Main Interface
    with st.container():
        # Header Section
        col1, col2 = st.columns([4,1])
        with col1:
            st.markdown("<div class='header'><h1>🧠 MindMate AI Companion</h1></div>", unsafe_allow_html=True)
        with col2:
            if st.button("Logout", use_container_width=True):
                for key in session_defaults.keys():
                    del st.session_state[key]
                st.rerun()
        
        # Tab Navigation
        tabs = st.tabs(["General Support 🌈", "Topic Support 🎯", "Symptom Analysis 🩺", "Chat History 📚"])
        
        # General Support Tab
        with tabs[0]:
            if st.session_state.session_id and st.session_state.current_session_type == 'general':
                render_chat_interface()
            else:
                st.markdown("### General Support")
                st.write("Start a casual conversation for emotional support")
                if st.button("Start General Session"):
                    st.session_state.session_id = create_session(st.session_state.user_id, "general")
                    st.session_state.current_session_type = "general"
                    st.session_state.current_topic = None
                    st.session_state.messages = []
                    st.rerun()

        # Topic Support Tab
        with tabs[1]:
            selected_topic = st.selectbox("Select Support Topic", 
                                        ["Anxiety", "Depression", "Relationships", "Stress"])
            
            if st.session_state.session_id and st.session_state.current_session_type == 'topic':
                render_chat_interface()
            else:
                st.markdown(f"### {selected_topic} Support")
                st.write("Get specialized support for your specific concerns")
                if st.button(f"Start {selected_topic} Session"):
                    st.session_state.session_id = create_session(
                        st.session_state.user_id, "topic", selected_topic)
                    st.session_state.current_session_type = "topic"
                    st.session_state.current_topic = selected_topic
                    st.session_state.messages = []
                    st.rerun()

        # Symptom Analysis Tab
        with tabs[2]:
            if st.session_state.session_id and st.session_state.current_session_type == 'diagnosis':
                render_chat_interface()
            else:
                st.markdown("### Symptom Analysis")
                st.write("Describe your symptoms for preliminary assessment")
                if st.button("Start Diagnosis Session"):
                    st.session_state.session_id = create_session(st.session_state.user_id, "diagnosis")
                    st.session_state.current_session_type = "diagnosis"
                    st.session_state.current_topic = None
                    st.session_state.messages = []
                    st.rerun()

        # Chat History Tab
        with tabs[3]:
            st.markdown("### Chat History")
            history = get_chat_history(st.session_state.user_id)
            
            if not history:
                st.info("No previous conversations found")
            else:
                for session in history:
                    session_id, session_type, topic, start_time, messages = session
                    with st.expander(f"{session_type.capitalize()} Session - {topic if topic else 'General'} ({start_time})"):
                        if messages:
                            message_list = messages.split('|||')
                            for msg in message_list:
                                is_user = "User: " in msg
                                if is_user:
                                    st.markdown(f"<div class='user-message'>{msg.replace('User: ', '')}</div>", 
                                                unsafe_allow_html=True)
                                else:
                                    st.markdown(f"<div class='bot-message'>{msg}</div>", 
                                                unsafe_allow_html=True)
                        else:
                            st.write("No messages in this session")

def render_chat_interface():
    st.markdown(f"### {st.session_state.current_topic or 'General'} Session")
    
    # Chat History Display
    for msg in st.session_state.messages:
        if msg['is_user']:
            st.markdown(f"<div class='user-message'>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            with st.chat_message("assistant"):
                with st.spinner("Generiving..."):
                    time.sleep(0.5)
                    st.markdown(msg['content'])
    
    # Message Handling
    if prompt := st.chat_input("How are you feeling today?"):
        # Store user message
        st.session_state.messages.append({"content": prompt, "is_user": True})
        
        # Emotion analysis
        emotion_result = emotion_chain.invoke({"message": prompt})
        score, emotion, reason = emotion_result.split("|")
        
        # Generate response
        chain = get_response_chain(
            st.session_state.current_session_type,
            st.session_state.current_topic
        )
        response = chain.invoke({
            "message": prompt,
            "topic": st.session_state.current_topic
        })
        
        # Store interaction
        conn = sqlite3.connect('mental_health.db')
        c = conn.cursor()
        c.execute("""INSERT INTO messages 
                    (session_id, content, is_user, sentiment_score, detected_emotion)
                    VALUES (?, ?, ?, ?, ?)""",
                  (st.session_state.session_id, prompt, True, score, emotion))
        c.execute("""INSERT INTO messages 
                    (session_id, content, is_user)
                    VALUES (?, ?, ?)""",
                  (st.session_state.session_id, response, False))
        conn.commit()
        conn.close()
        
        st.session_state.messages.append({"content": response, "is_user": False})
        st.rerun()

if __name__ == "__main__":
    main()