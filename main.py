import streamlit as st
from streamlit_option_menu import option_menu
from pages import AUDIO_TRANSCRIPTION_WITH_AI, ONLINE_LLM_INTEGRATION, IMAGE_ANALYSIS_WITH_AI, GPT4_DOCUMENTS_ANALYSIS, DOCUMENTS_UPLOAD_PAGE
import os

# Set up Streamlit page config
# st.set_page_config(page_title="ChatPDF", page_icon=":robot_face:", layout="wide")

# Custom CSS and JavaScript for enhanced UI
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

# Function to handle file upload and reading
def read_and_save_file():
    # Placeholder function to handle file reading
    st.session_state["file_uploaded"] = True
    st.session_state["messages"].append({"role": "system", "content": "File uploaded and processed."})

# Function to process user input
def process_input():
    user_input = st.session_state["user_input"]
    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        st.session_state["user_input"] = ""  # Clear the input field

# Function to display messages
def display_messages():
    if "messages" in st.session_state:
        for msg in st.session_state["messages"]:
            if msg["role"] == "user":
                st.markdown(f"<div class='message user'>{msg['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='message agent'>{msg['content']}</div>", unsafe_allow_html=True)

# Home page function
def home_page():
    st.markdown("<div class='centered-logo'>", unsafe_allow_html=True)
    st.image('images/logo_m.jpg', width=200)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.header("ChatPDF")

    st.subheader("Upload a document")
    st.file_uploader(
        "Upload document",
        type=["pdf"],
        key="file_uploader",
        on_change=read_and_save_file,
        label_visibility="collapsed",
        accept_multiple_files=True,
    )

    st.session_state["ingestion_spinner"] = st.empty()
    
    display_messages()
    st.text_input("Message", key="user_input", on_change=process_input)

# Main application page
def page():
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    home_page()

if __name__ == "__main__":
    page()
