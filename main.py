import streamlit as st
from streamlit_option_menu import option_menu
from pages import AUDIO_TRANSCRIPTION_WITH_AI, ONLINE_LLM_INTEGRATION, IMAGE_ANALYSIS_WITH_AI, GPT4_DOCUMENTS_ANALYSIS, DOCUMENTS_UPLOAD_PAGE
import os
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


st.markdown(
    """
    <style>
    body {
        font-family: 'Arial', sans-serif;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    .main-menu {
        border-radius: 10px;
        overflow: hidden;
    }
    .main-menu > div {
        background-color: #343a40;
        color: #fff;
        padding: 10px;
        margin-bottom: 5px;
        transition: background-color 0.3s ease;
    }
    .main-menu > div:hover {
        background-color: #495057;
    }
    .message {
        border-radius: 10px;
        margin-bottom: 10px;
        padding: 10px;
        animation: fadeIn 0.5s ease-in;
    }
    .message.user {
        background-color: #d1e7dd;
        text-align: right;
    }
    .message.agent {
        background-color: #f8d7da;
        text-align: left;
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    .centered-logo {
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


def home_page():
    st.markdown("<div class='centered-logo'>", unsafe_allow_html=True)
    st.image('images/logo_m.png', width=200)
    st.markdown("</div>", unsafe_allow_html=True)
    st.header("Welcome Page: AIChatPDF")
   

    st.markdown("### You can upload a document to ask the assistant about it.")  
    st.success("All models are connected. The status is up.")

    

    st.session_state["ingestion_spinner"] = st.empty()
    
 
def page():
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    home_page()

if __name__ == "__main__":
    page()