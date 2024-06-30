import streamlit as st
import PyPDF2
import logging
from langchain.embeddings import OpenAIEmbeddings
from pinecone import Pinecone, ServerlessSpec
from pymongo import MongoClient
import gridfs

# Set logging level
logging.basicConfig(level=logging.INFO)

# Set your API key for embeddings
api_key = "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"

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

# Streamlit interface
def embed_page():
    st.markdown("<div class='centered-logo'>", unsafe_allow_html=True)
    st.image('images/logo_m.jpg', width=200)
    st.markdown("</div>", unsafe_allow_html=True)
    st.title("Upload and Embed PDF")

    # File uploader for PDF
    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

    if uploaded_file:
        pdf_text = extract_text_from_pdf(uploaded_file)
        if pdf_text:
            add_pdf_to_pinecone(pdf_text)
            save_pdf_to_mongodb(uploaded_file, pdf_text)
            st.session_state["pdf_text"] = pdf_text  # Store PDF text in session state
            st.success("PDF content has been added to the model context and saved .")
            logging.info(f"PDF text: {pdf_text}")  # Log the PDF text
        else:
            st.error("Failed to extract text from PDF.")

if __name__ == "__main__":
    embed_page()
