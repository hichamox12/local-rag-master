import streamlit as st
import PyPDF2
import logging
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage
from langchain.chains import LLMChain
from langchain.embeddings import OpenAIEmbeddings
from pinecone import Pinecone, ServerlessSpec
from pymongo import MongoClient
import gridfs
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

# Ensure this name is 45 characters or less
existing_indexes = pc.list_indexes().names()
if index_name not in existing_indexes:
    pc.create_index(
        name=index_name,
        dimension=1536,  # Adjust dimension to match your embeddings
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")  # Adjust the region to a valid one
    )
else:
    logging.info(f"Index '{index_name}' already exists. Using the existing index.")

index = pc.Index(index_name)

# Initialize MongoDB client
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["document_db"]
fs = gridfs.GridFS(db)

# Function to extract text from PDF
def extract_text_from_pdf(file):
    try:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text()
        return text
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return ""

# Function to add PDF text to Pinecone
def add_pdf_to_pinecone(pdf_text):
    vectors = embeddings.embed_documents([pdf_text])
    for i, vector in enumerate(vectors):
        metadata = {"text": pdf_text}  # Ensure metadata is included
        index.upsert([(f"pdf-{i}", vector, metadata)])

# Function to save PDF to MongoDB
def save_pdf_to_mongodb(file, pdf_text):
    file_id = fs.put(file, filename=file.name)
    db.documents.insert_one({"filename": file.name, "file_id": file_id, "text": pdf_text})

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
        placeholder.markdown(f"<div class='assistant-response'>{full_response}</div>", unsafe_allow_html=True)
        await asyncio.sleep(0.1)  # Simulate streaming delay
    return full_response

# SVG robot icon

# Function to add default robot icon


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

# Streamlit interface
def app():
   
    st.title("GPT-4 Chatbot with PDF")

    # File uploader for PDF
    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

    if uploaded_file:
        pdf_text = extract_text_from_pdf(uploaded_file)
        if pdf_text:
           # st.write("Extracted PDF text:")
            # st.write(pdf_text)
            add_pdf_to_pinecone(pdf_text)
            save_pdf_to_mongodb(uploaded_file, pdf_text)
            st.write("PDF content has been added to the model context and saved to MongoDB.")
            logging.info(f"PDF text: {pdf_text}")  # Log the PDF text
            print("PDF text extraction successful")
        else:
            st.write("Failed to extract text from PDF.")
            print("Failed to extract text from PDF")

    prompt = st.text_input("Enter your prompt:")

    if st.button("Submit"):
        if prompt:
            response_placeholder = st.empty()
            with st.spinner("Generating response..."):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(stream_response(prompt, pdf_text, response_placeholder))
        else:
            st.write("Please enter a prompt.")

if __name__ == "__main__":
    app()
