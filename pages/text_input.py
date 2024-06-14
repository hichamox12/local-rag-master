import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import nest_asyncio
import asyncio

# Set your API Key
os.environ["GOOGLE_API_KEY"] = 'AIzaSyCAccFwkLEiwJ_owYjmUmlqEx9joaANyTA'

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Function to generate text response using Gemini Pro
async def generate_gemini_response(prompt):
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-pro")
        result = llm.invoke(prompt)
        response_content = result.content  # Access the content of the result message
        for i in range(0, len(response_content), 10):  # Chunk size of 10 characters
            yield response_content[i:i+10]
            await asyncio.sleep(0.1)  # Simulate streaming delay
    except Exception as e:
        yield f"An error occurred: {str(e)}"

# Wrapper to run the async function and stream results
def get_text_response(prompt, model):
    if model == "Google Gemini Pro":
        return generate_gemini_response(prompt)

async def stream_response(prompt, model, placeholder):
    response_generator = get_text_response(prompt, model)
    full_response = ""
    async for chunk in response_generator:
        full_response += chunk
        placeholder.markdown(f"<div class='assistant-response'>{full_response}</div>", unsafe_allow_html=True)

# Custom CSS for styling
st.markdown(
    """
    <style>
    .assistant-response {
        background-color: #f0f0f0;
        border-radius: 10px;
        padding: 10px;
        margin-top: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def app():
    st.title("Gemini Chatbot")
    
    model_options = ["Google Gemini Pro"]
    selected_model = st.selectbox("Choose the model to generate a response:", model_options)
    
    user_input = st.text_input("Enter your message here:")
    
    if user_input and st.button("Submit"):
        response_placeholder = st.empty()
        with st.spinner("Generating response..."):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(stream_response(user_input, selected_model, response_placeholder))

if __name__ == "__main__":
    app()
