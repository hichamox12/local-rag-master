import streamlit as st
import logging
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage
from langchain.chains import LLMChain
from langchain.embeddings import OpenAIEmbeddings
from pinecone import Pinecone
import asyncio

# Set logging level
logging.basicConfig(level=logging.INFO)

# Set your GPT-4 API key
api_key = "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"

# Initialize the OpenAI LLM with the GPT-4 model
llm = ChatOpenAI(model_name="gpt-4", openai_api_key=api_key)

# Define the prompt template
prompt_template = ChatPromptTemplate.from_template("You are a helpful assistant. {prompt}")

# Create the LLM chain
chain = LLMChain(llm=llm, prompt=prompt_template)

# Initialize embeddings
embeddings = OpenAIEmbeddings(openai_api_key=api_key)

# Initialize Pinecone
pinecone_api_key = "a134614e-8a1a-47ea-8483-a5aa51a9f1f7"
pc = Pinecone(api_key=pinecone_api_key)
index_name = "quicksart"
index = pc.Index(index_name)

# Function to test GPT-4 API with embeddings
def test_gpt4_api_with_embeddings(prompt, pdf_text):
    query_vector = embeddings.embed_query(prompt)
    results = index.query(vector=query_vector, top_k=1)
    context = ""
    if results.matches:
        match = results.matches[0]
        if match.metadata and "text" in match.metadata:
            context = match.metadata["text"]

    messages = [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content=f"Context from PDF:\n{context}\n\n{prompt} {pdf_text}")
    ]
    logging.info("Messages sent to the language model: %s", messages)

    response = chain.run(messages)
    return response

# Stream response function
async def stream_response(prompt, pdf_text, placeholder):
    response = test_gpt4_api_with_embeddings(prompt, pdf_text)
    full_response = ""
    for i in range(0, len(response), 10):  # Chunk size of 10 characters
        full_response += response[i:i+10]
        placeholder.markdown(f"<div class='assistant-response'><img src='https://cdn-icons-png.flaticon.com/512/3398/3398643.png' class='avatar'><span>{full_response}</span></div>", unsafe_allow_html=True)
        await asyncio.sleep(0.1)  # Simulate streaming delay
    return full_response

# Custom CSS for styling and dynamic scrolling
st.markdown(
    """
    <style>
    .assistant-response, .user-message {
        display: flex;
        align-items: center;
        gap: 10px;
        border-radius: 12px;
        padding: 14px;
        margin-top: 8px;
        width: 100%;
    }
    .assistant-response {
        background-color: #f0f0f0;
        flex-direction: row-reverse;
    }
    .user-message {
        background-color: #d1e7dd;
        text-align: right;
    }
    .message-container {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 10px;
        overflow-y: auto;
        width: 100%;
        padding-top: 10px;  /* Adjust padding to match fixed input field height */
    }
    .input-container {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        padding: 16px;
        background: white;
        border-bottom: 1px solid #e6e6e6;
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
    .centered-title {
        text-align: center;
        margin-top: 10px;  /* Adjust margin to ensure title is below fixed input */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# # JavaScript to scroll to the bottom of the message container
# scroll_js = """
# <script>
# function scrollToBottom() {
#     var container = document.querySelector('.message-container');
#     container.scrollTop = container.scrollHeight;
# }
# document.addEventListener("DOMContentLoaded", scrollToBottom);
# </script>
# """

# st.markdown(scroll_js, unsafe_allow_html=True)

# Streamlit interface for conversation
def conversation_page():
    st.markdown("<div class='centered-logo'>", unsafe_allow_html=True)
    st.image('images/logo_m.jpg', width=200)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<h1 class='centered-title'>GPT-4 Chatbot with PDF</h1>", unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Input container
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    prompt = st.text_input("Enter your prompt:", key="user_input")
    if st.button("Submit"):
        if prompt:
            pdf_text = st.session_state.get("pdf_text", "")
            if not pdf_text:
                st.error("No PDF content available. Please upload a PDF first.")
                return
            
            # Add user message to the session state
            st.session_state["messages"].append({"role": "user", "content": prompt})
            response_placeholder = st.empty()

            with st.spinner("Generating response..."):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                full_response = loop.run_until_complete(stream_response(prompt, pdf_text, response_placeholder))

                # Add the assistant's response to the session state dynamically
                response_placeholder.empty()
                st.session_state["messages"].append({"role": "assistant", "content": full_response})

            # Scroll to the bottom to show the latest message
            st.markdown('<script>scrollToBottom();</script>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Messages container
    st.markdown('<div class="message-container">', unsafe_allow_html=True)
    message_container = st.container()
    with message_container:
        for msg in st.session_state["messages"]:
            if msg["role"] == "user":
                st.markdown(f"<div class='user-message'><img src='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTtKoP1jSRN1n8cqppT7X3zPlbcJwZECr43qA&s' class='avatar'><span>{msg['content']}</span></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='assistant-response'><img src='https://cdn-icons-png.flaticon.com/512/3398/3398643.png' class='avatar'><span>{msg['content']}</span></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Clear Messages button
    if st.button("Clear Messages"):
        st.session_state["messages"] = []

if __name__ == "__main__":
    conversation_page()
