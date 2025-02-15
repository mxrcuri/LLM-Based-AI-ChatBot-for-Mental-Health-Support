# llm.py
import streamlit as st  # You might replace this with os.environ if you prefer
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
GOOGLE_API_KEY="AIzaSyBHtfggtV7H2u3jEj0i35yX71XYqDwjFd4"

def init_gemini():
    # You can load the API key from st.secrets or from environment variables.
    return ChatGoogleGenerativeAI(
        model="gemini-pro",
        temperature=0.7,
        google_api_key=st.secrets["GOOGLE_API_KEY"]  # or use os.environ["GOOGLE_API_KEY"]
    )

def get_emotion_analysis(message: str) -> str:
    # Build an emotion analysis prompt
    prompt = ChatPromptTemplate.from_template(
        "Analyze the emotion in this message on a scale of 1-10 (1 = very negative, 10 = very positive). Format: score|emotion|short_reason. Message: {message}"
    )
    # Chain the prompt with the LLM and output parser
    chain = prompt | init_gemini() | StrOutputParser()
    result = chain.invoke({"message": message})
    return result

def get_response(message: str, session_type: str, topic: str = None) -> str:
    # Choose a prompt based on the session type.
    if session_type == "diagnosis":
        prompt = ChatPromptTemplate.from_template(
            "As a mental health diagnosis assistant, analyze these symptoms: {message}. Consider possible conditions and next steps. Respond succinctly."
        )
    elif session_type == "topic":
        prompt = ChatPromptTemplate.from_template(
            "You're a specialist counselor for {topic}. Respond to: {message} using evidence-based techniques."
        )
    else:
        prompt = ChatPromptTemplate.from_template(
            "You're a compassionate mental health companion. Respond to: {message} using supportive language."
        )
    
    # Build the chain to generate a response
    chain = prompt | init_gemini() | StrOutputParser()
    result = chain.invoke({"message": message, "topic": topic})
    return result
