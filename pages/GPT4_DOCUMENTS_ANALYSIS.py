import streamlit as st
import logging
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage
from langchain.chains import LLMChain
from langchain.embeddings import OpenAIEmbeddings
from pinecone import Pinecone
import asyncio


logging.basicConfig(level=logging.INFO)


api_key = "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"

llm = ChatOpenAI(model_name="gpt-4o", openai_api_key=api_key)


prompt_template = ChatPromptTemplate.from_template("You are a helpful assistant. {prompt}")


chain = LLMChain(llm=llm, prompt=prompt_template)


embeddings = OpenAIEmbeddings(openai_api_key=api_key)


pinecone_api_key = "a134614e-8a1a-47ea-8483-a5aa51a9f1f7"
pc = Pinecone(api_key=pinecone_api_key)
index_name = "quicksart"
index = pc.Index(index_name)


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
        HumanMessage(content=f"Context from PDF:\n\n\n{prompt} {pdf_text}")
    ]
    logging.info("Messages sent to the language model: %s", messages)

    response = chain.run(messages)
    return response


async def stream_response(prompt, pdf_text, placeholder):
    response = test_gpt4_api_with_embeddings(prompt, pdf_text)
    full_response = ""
    for i in range(0, len(response), 10):  
        full_response += response[i:i+10]
        placeholder.markdown(f"<div class='assistant-response'><img src='https://cdn-icons-png.flaticon.com/512/3398/3398643.png' class='avatar'><span>{full_response}</span></div>", unsafe_allow_html=True)
        await asyncio.sleep(0.1)  
    return full_response

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
        background-color: #262730;
        color: #fff;
    }
    .user-message {
        background-color: #a4ffa1;
        color: #000;
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
  
    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
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


def GPT4_DOCUMENTS_ANALYSIS():
    st.markdown("<div class='centered-logo'>", unsafe_allow_html=True)
    st.image('images/logo_m.png', width=200)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<h1 class='centered-title'>GPT-4 Chatbot with PDF</h1>", unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    prompt = st.text_input("Enter your prompt:", key="user_input")
    if st.button("Submit"):
        if prompt:
            pdf_text = st.session_state.get("pdf_text", "")
            if not pdf_text:
                st.error("No PDF content available. Please upload a PDF first.")
                return
            
            st.session_state["messages"].append({"role": "user", "content": prompt})
            response_placeholder = st.empty()

            with st.spinner("Generating response..."):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                full_response = loop.run_until_complete(stream_response(prompt, pdf_text, response_placeholder))

               
                response_placeholder.empty()
                st.session_state["messages"].append({"role": "assistant", "content": full_response})

            st.markdown('<script>scrollToBottom();</script>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="message-container">', unsafe_allow_html=True)
    message_container = st.container()
    with message_container:
        for msg in st.session_state["messages"]:
            if msg["role"] == "user":
                st.markdown(f"<div class='user-message'><img src='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTtKoP1jSRN1n8cqppT7X3zPlbcJwZECr43qA&s' class='avatar'><span>{msg['content']}</span></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='assistant-response'><img src='https://cdn-icons-png.flaticon.com/512/3398/3398643.png' class='avatar'><span>{msg['content']}</span></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("Clear Messages"):
        st.session_state["messages"] = []

if __name__ == "__main__":
    GPT4_DOCUMENTS_ANALYSIS()