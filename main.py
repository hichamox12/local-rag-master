import os
import tempfile
import streamlit as st
from streamlit_chat import message
from streamlit_option_menu import option_menu
from rag import ChatPDF
from pages import audio_whisper, text_input, image_generation, filehandler, pdfhandler  # Ensure pdfhandler is correctly imported
from pymongo import MongoClient
import hashlib

# Set up Streamlit page config
st.set_page_config(page_title="ChatPDF")

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["document_db"]
users_collection = db["users"]

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Display messages
def display_messages():
    st.subheader("Chat")
    for i, (msg, is_user) in enumerate(st.session_state["messages"]):
        message(msg, is_user=is_user, key=str(i))
    st.session_state["thinking_spinner"] = st.empty()

# Process user input
def process_input():
    if st.session_state["user_input"] and len(st.session_state["user_input"].strip()) > 0:
        user_text = st.session_state["user_input"].strip()
        with st.session_state["thinking_spinner"], st.spinner("Thinking..."):
            agent_text = st.session_state["assistant"].ask(user_text)
        
        st.session_state["messages"].append((user_text, True))
        st.session_state["messages"].append((agent_text, False))

# Read and save file
def read_and_save_file():
    st.session_state["assistant"].clear()
    st.session_state["messages"] = []
    st.session_state["user_input"] = ""

    for file in st.session_state["file_uploader"]:
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(file.getbuffer())
            file_path = tf.name

        with st.session_state["ingestion_spinner"], st.spinner(f"Ingesting {file.name}"):
            st.session_state["assistant"].ingest(file_path)
        os.remove(file_path)

# Home page
def home_page():
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

# Sign-up page
def sign_up_page():
    st.title("Sign Up")
    email = st.text_input("Email Address")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    
    if st.button("Sign Up"):
        if password != confirm_password:
            st.error("Passwords do not match!")
        elif users_collection.find_one({"email": email}):
            st.error("Email already exists!")
        elif users_collection.find_one({"username": username}):
            st.error("Username already exists!")
        else:
            hashed_password = hash_password(password)
            users_collection.insert_one({"email": email, "username": username, "password": hashed_password})
            st.success("Account created successfully!")
            st.info("Please go to the Login page to sign in.")

# Login page
def login_page():
    st.title("Login")
    email = st.text_input("Email Address")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = users_collection.find_one({"email": email, "password": hash_password(password)})
        if user:
            st.session_state["authenticated"] = True
            st.session_state["username"] = user["username"]
            st.session_state["email"] = user["email"]
        else:
            st.error("Invalid credentials")

# Main application page
def page():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        auth_option = st.selectbox("Select an option", ["Login", "Sign Up"])
        if auth_option == "Login":
            login_page()
        elif auth_option == "Sign Up":
            sign_up_page()
    else:
        if "messages" not in st.session_state:
            st.session_state["messages"] = []
        if "assistant" not in st.session_state:
            st.session_state["assistant"] = ChatPDF()

        selected = option_menu(
            menu_title="Main Menu",
            options=["Home", "Audio Whisper", "Text Input", "Image Generation", "File Handler", "PDF Handler"],
            icons=["house", "mic", "keyboard", "image", "file", "file-text"],
            menu_icon="cast",
            default_index=0,
        )

        if selected == "Home":
            home_page()
        elif selected == "Audio Whisper":
            audio_whisper.app()
        elif selected == "Text Input":
            text_input.app()
        elif selected == "Image Generation":
            image_generation.app()
        elif selected == "File Handler":
            filehandler.app()
        elif selected == "PDF Handler":
            pdfhandler.app()  # Include pdfhandler

if __name__ == "__main__":
    page()
