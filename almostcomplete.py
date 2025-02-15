import streamlit as st
from google.generativeai import GenerativeModel
import google.generativeai as genai

# Configure Google API key
genai.configure(api_key="AIzaSyBHtfggtV7H2u3jEj0i35yX71XYqDwjFd4")
model = GenerativeModel("gemini-pro")

# Streamlit page setup
st.set_page_config(page_title="Solace - A Safe Space", layout="wide")

# Custom styles
st.markdown(
    """
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
        .description {
            font-family: 'Inria Serif', serif;
            font-size: 1.2rem;
            text-align: center;
        }
        .quote {
            font-family: 'Acme', sans-serif;
            color: #F88379;
            font-size: 1.5rem;
            text-align: center;
            margin-top: 20px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Display title and introduction
st.markdown("<div class='main-title'>Solace</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>A Safe Space for Mental Well-being</div>", unsafe_allow_html=True)

st.markdown(
    """
    <div class='description'>
    Welcome to Solace, your safe space to breathe, reflect, and heal. Life can feel overwhelming at times, and we’re here to remind you that you don’t have to face it alone. 
    Solace is more than just a website—it’s a companion on your mental health journey, offering tools, support, and a listening ear whenever you need it.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='quote'>“Take a deep breath—you’ve found your place of peace”</div>", unsafe_allow_html=True)

# Features section
st.subheader("Your Free Personal AI Therapist")
st.write(
    "Measure & improve your mental health in real time with your personal AI chatbot. No sign-up. Available 24/7. Daily insights just for you!"
)

# Chatbot logic
st.subheader("Chat with Penguin 🐧")
user_input = st.text_input("How can I help you today?", "")
if user_input:
    response = model.generate_content(user_input)
    st.text_area("Penguin:", response.text, height=200)
