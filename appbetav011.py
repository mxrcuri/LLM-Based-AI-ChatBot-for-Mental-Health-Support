import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
from google.generativeai import GenerativeModel
import google.generativeai as genai

# --------------------------
# Page Configuration (MUST BE FIRST)
# --------------------------
st.set_page_config(
    page_title="Solace - A Safe Space",
    page_icon="🤗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --------------------------
# Configure Gemini
# --------------------------
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = GenerativeModel("gemini-pro")

# --------------------------
# Custom Styles
# --------------------------
st.markdown("""
<style>
    .main-title {
        font-family: 'Aladin', cursive;
        color: #F88379;
        font-size: 4rem;
        text-align: center;
    }
    .subtitle {
        font-family: 'Inter', sans-serif;
        color: #8A8C91;
        font-size: 2rem;
        text-align: center;
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
    .session-card {
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.2s ease;
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
                  start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  end_time TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id INTEGER,
                  content TEXT,
                  is_user BOOLEAN,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(session_id) REFERENCES sessions(id))''')
    
    conn.commit()
    conn.close()

init_db()

# --------------------------
# Authentication
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
# Session Management
# --------------------------
def create_session(user_id, session_type):
    conn = sqlite3.connect('mental_health.db')
    c = conn.cursor()
    c.execute("INSERT INTO sessions (user_id, session_type) VALUES (?, ?)",
              (user_id, session_type))
    session_id = c.lastrowid
    conn.commit()
    conn.close()
    return session_id

# --------------------------
# Main App Logic
# --------------------------
def main():
    # Session State
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None

    # Authentication Gate
    if not st.session_state.user_id:
        show_auth()
        return

    # Main Interface
    show_main_interface()

def show_auth():
    st.markdown("<div class='main-title'>Solace</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Your Safe Space for Mental Well-being</div>", unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            auth_choice = st.radio("Choose Action", ["Login", "Register"], horizontal=True)
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if auth_choice == "Register":
                confirm_password = st.text_input("Confirm Password", type="password")
            
            if st.button("Continue"):
                handle_auth(auth_choice, username, password, 
                           confirm_password if auth_choice == "Register" else None)

def handle_auth(action, username, password, confirm_password=None):
    if action == "Register":
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

def show_main_interface():
    # Header
    st.markdown("<div class='main-title'>Solace</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Your Companion in Mental Well-being</div>", unsafe_allow_html=True)
    
    # Navigation
    tabs = st.tabs(["Chat 🐧", "History 📚", "Resources 📖"])
    
    with tabs[0]:
        show_chat_interface()
    
    with tabs[1]:
        show_history()
    
    with tabs[2]:
        show_resources()
    
    # Logout
    if st.button("Logout", key="logout"):
        reset_session()

def show_chat_interface():
    def classify_issue(user_input):
        categories = {
            "Anxiety": ["nervous", "worried", "overwhelmed", "stressed", "panic"],
            "Depression": ["sad", "hopeless", "tired", "worthless", "lost"],
            "Relationship": ["breakup", "partner", "trust", "cheated", "argument"],
            "Self-Esteem": ["ugly", "unworthy", "not good enough", "hate myself"],
            "Burnout": ["exhausted", "drained", "no motivation"],
        }
        for category, keywords in categories.items():
            if any(kw in user_input.lower() for kw in keywords):
                return category
        return "General Stress"

    # Chat History
    for msg in st.session_state.messages:
        if msg['is_user']:
            st.markdown(f"<div class='user-message'>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='bot-message'>{msg['content']}</div>", unsafe_allow_html=True)

    # Input Handling
    if prompt := st.chat_input("How can I help you today?"):
        # Start session if not exists
        if not st.session_state.session_id:
            st.session_state.session_id = create_session(st.session_state.user_id, "chat")
        
        # Classify and respond
        issue_type = classify_issue(prompt)
        response = generate_response(prompt, issue_type)
        
        # Store messages
        store_message(prompt, True)
        store_message(response, False)
        
        st.session_state.messages.append({"content": prompt, "is_user": True})
        st.session_state.messages.append({"content": response, "is_user": False})
        st.rerun()

def generate_response(prompt, issue_type):
    prompt_template = f"""
    As a mental health companion, respond to this {issue_type} concern: {prompt}
    Provide compassionate support with practical suggestions. 
    Use simple language and keep response under 150 words.
    
    """
    response = model.generate_content(prompt_template)
    return response.text

def store_message(content, is_user):
    conn = sqlite3.connect('mental_health.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (session_id, content, is_user) VALUES (?, ?, ?)",
              (st.session_state.session_id, content, is_user))
    conn.commit()
    conn.close()

def show_history():
    conn = sqlite3.connect('mental_health.db')
    c = conn.cursor()
    c.execute('''SELECT s.id, s.start_time, GROUP_CONCAT(m.content, '|||') 
               FROM sessions s LEFT JOIN messages m ON s.id = m.session_id 
               WHERE s.user_id = ? GROUP BY s.id''', (st.session_state.user_id,))
    
    for session in c.fetchall():
        with st.expander(f"Session - {session[1]}"):
            if session[2]:
                for msg in session[2].split('|||'):
                    if "User: " in msg:
                        st.markdown(f"<div class='user-message'>{msg.replace('User: ', '')}</div>", 
                                   unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='bot-message'>{msg}</div>", 
                                   unsafe_allow_html=True)

def show_resources():
    st.markdown("### Mental Health Resources")
    resources = {
        "Crisis Hotlines": ["National Suicide Prevention Lifeline: 1-800-273-TALK (8255)",
                           "Crisis Text Line: Text HOME to 741741"],
        "Self-Help Tools": ["MindShift CBT App", "Calm Meditation App"],
        "Educational Content": ["Understanding Anxiety (PDF Guide)", 
                              "Building Resilience Workshop Recording"]
    }
    
    for category, items in resources.items():
        with st.expander(category):
            for item in items:
                st.write(f"- {item}")

def reset_session():
    st.session_state.user_id = None
    st.session_state.messages = []
    st.session_state.session_id = None
    st.rerun()

if __name__ == "__main__":
    main()
