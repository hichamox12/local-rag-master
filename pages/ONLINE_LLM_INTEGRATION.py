import streamlit as st
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
import openai
import os
import nest_asyncio
import asyncio

# Set your API Keys
os.environ["GOOGLE_API_KEY"] = 'AIzaSyCAccFwkLEiwJ_owYjmUmlqEx9joaANyTA'
openai.api_key = "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"

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Function to generate text response using Google Gemini Pro
async def generate_gemini_response(prompt):
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-pro")
        result = llm.invoke(prompt)
        response_content = result.content  # Access the content of the result message
        for i in range(0, len(response_content), 10):  # Chunk size of 10 characters
            yield response_content[i:i+10]
            await asyncio.sleep(0.1)
    except Exception as e:
        yield f"An error occurred: {str(e)}"

# Function to generate text response using GPT-4
async def generate_gpt4_response(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            stream=True
        )
        for chunk in response:
            if 'choices' in chunk and len(chunk['choices']) > 0:
                if 'delta' in chunk['choices'][0] and 'content' in chunk['choices'][0]['delta']:
                    yield chunk['choices'][0]['delta']['content']
                    await asyncio.sleep(0.1)
    except Exception as e:
        yield f"An error occurred: {str(e)}"

# Wrapper to run the async function and stream results
def get_text_response(prompt, model):
    if model == "Google Gemini Pro":
        return generate_gemini_response(prompt)
    elif model == "GPT-4":
        return generate_gpt4_response(prompt)

async def fetch_full_response(prompt, model):
    response_generator = get_text_response(prompt, model)
    full_response = ""
    async for chunk in response_generator:
        full_response += chunk
    return full_response

# Function to handle user input submission
def handle_submit():
    user_input = st.session_state["user_input"]
    if user_input:
        # Add user message to the session state
        st.session_state["messages"].append({"role": "user", "content": user_input})
        
        # Placeholder for the assistant's response
        response_placeholder = st.empty()

        # Determine the selected model
        selected_model = st.session_state.get("selected_model", "GPT-4")

        with st.spinner("Generating response..."):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            full_response = loop.run_until_complete(fetch_full_response(user_input, selected_model))

            # Add the assistant's response to the session state
            st.session_state["messages"].append({"role": "assistant", "content": full_response})
        
        # Clear the user input
        st.session_state["user_input"] = ""
        # Scroll to the bottom to show the latest message
        st.markdown('<script>scrollToBottom();</script>', unsafe_allow_html=True)

# Custom CSS for styling
st.markdown(
    """
    <style>
    .assistant-response, .user-message {
        display: flex;
        align-items: center;
        gap: 10px;
        border-radius: 10px;
        padding: 10px;
        margin-top: 10px;
        width: 100%;
    }
    .assistant-response {
        background-color: #f0f0f0;
    }
    .user-message {
        background-color: #d1e7dd;
        text-align: right;
        flex-direction: row-reverse;
    }
    .message-container {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 10px;
        overflow-y: auto;
        width: 100%;
    }
    .input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 10px;
        background: white;
        border-top: 1px solid #e6e6e6;
        z-index: 1000;
    }
    .dropdown-container {
        position: sticky;
        top: 0;
        background: white;
        padding: 10px 0;
        z-index: 1000;
    }
    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# JavaScript to scroll to the bottom of the message container
scroll_js = """
<script>
function scrollToBottom() {
    var container = document.querySelector('.message-container');
    container.scrollTop = container.scrollHeight;
}
</script>
"""

st.markdown(scroll_js, unsafe_allow_html=True)

# Main app function
def app():
    st.markdown("<div class='centered-logo'>", unsafe_allow_html=True)
    st.image('images/logo_m.jpg', width=200)
    st.markdown("</div>", unsafe_allow_html=True)
    st.title("CHATBOTS INTERFACE")

    # Dropdown container
    st.markdown('<div class="dropdown-container">', unsafe_allow_html=True)
    model_options = ["Google Gemini Pro", "GPT-4"]
    selected_model = st.selectbox("", model_options, key="selected_model")
    st.markdown('</div>', unsafe_allow_html=True)

    # Messages container
    st.markdown('<div class="message-container">', unsafe_allow_html=True)
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    for msg in st.session_state["messages"]:
        if msg["role"] == "user":
            st.markdown(f"<div class='user-message'><img src='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTtKoP1jSRN1n8cqppT7X3zPlbcJwZECr43qA&s' class='avatar' style='width: 40px; height: 40px;'><span>{msg['content']}</span></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='assistant-response'><img src='https://cdn-icons-png.flaticon.com/512/3398/3398643.png' class='avatar' style='width: 40px; height: 40px;'><span>{msg['content']}</span></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Input container
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    st.text_input("Enter your message here:", key="user_input", on_change=handle_submit)
    st.markdown('</div>', unsafe_allow_html=True)

# Clear Messages button
    if st.button("Clear Messages"):
        st.session_state["messages"] = []


if __name__ == "__main__":
    app()
