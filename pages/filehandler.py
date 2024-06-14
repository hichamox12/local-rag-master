import pandas as pd
from PyPDF2 import PdfReader
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from huggingface_hub import login
import streamlit as st
from io import StringIO
from sentence_transformers import SentenceTransformer
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document
from pymongo import MongoClient
from bson.binary import Binary
from pinecone import Pinecone, ServerlessSpec

# Set your Hugging Face API token
hf_token = "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"
login(hf_token)

# Initialize Pinecone
pinecone_api_key = "a134614e-8a1a-47ea-8483-a5aa51a9f1f7"
pc = Pinecone(api_key=pinecone_api_key)
index_name = "quickstart"  # Ensure this name is 45 characters or less
existing_indexes = pc.list_indexes().names()

if index_name not in existing_indexes:
    pc.create_index(
        name=index_name,
        dimension=384,  # Adjust dimension to match your embeddings
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")  # Adjust the region to a valid one
    )
else:
    print(f"Index '{index_name}' already exists. Using the existing index.")

index = pc.Index(index_name)

# MongoDB setup
mongo_client = MongoClient("mongodb://localhost:27017/")  # Update with your MongoDB connection string
db = mongo_client["document_db"]
pdf_collection = db["pdf_files"]

# Load the model from Hugging Face for summarization
model_name = "facebook/bart-large-cnn"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

# Load the embeddings model
embeddings_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Function to read text from PDF
def read_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Function to read text from CSV
def read_csv(file):
    df = pd.read_csv(file)
    return df.to_string()

# Function to read text from Excel
def read_excel(file):
    df = pd.read_excel(file)
    return df.to_string()

# Function to process text input for summarization
def process_text(input_text):
    inputs = tokenizer.encode("summarize: " + input_text, return_tensors="pt", max_length=512, truncation=True)
    summary_ids = model.generate(inputs, max_length=150, min_length=40, length_penalty=2.0, num_beams=4, early_stopping=True)
    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)

# Function to store PDF in MongoDB
def store_pdf(file, file_name):
    file_data = file.read()
    pdf_collection.insert_one({
        "file_name": file_name,
        "file_data": Binary(file_data)
    })

# Custom CSS for styling
st.markdown(
    """
    <style>
    .summary-response {
        background-color: #f0f0f0;
        border-radius: 10px;
        padding: 10px;
        margin-top: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Streamlit app
def app():
    st.title("Document Analyzer")

    uploaded_file = st.file_uploader("Upload a file", type=["pdf", "csv", "txt", "xlsx"])

    if uploaded_file is not None:
        file_name = uploaded_file.name
        file_type = file_name.split('.')[-1]

        if file_type == "pdf":
            text = read_pdf(uploaded_file)
            uploaded_file.seek(0)  # Reset file pointer after reading
            store_pdf(uploaded_file, file_name)  # Store the PDF file in MongoDB
        elif file_type == "csv":
            text = read_csv(uploaded_file)
        elif file_type == "xlsx":
            text = read_excel(uploaded_file)
        elif file_type == "txt":
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            text = stringio.read()

        # Summarize the document
        summary = process_text(text)
        st.markdown(f"<div class='summary-response'>{summary}</div>", unsafe_allow_html=True)

        # Split text into smaller chunks for embedding
        text_splitter = CharacterTextSplitter()
        texts = text_splitter.split_text(text)

        # Create Document objects
        documents = [Document(page_content=text) for text in texts]

        # Create embeddings for the documents
        embeddings = embeddings_model.encode([doc.page_content for doc in documents])

        # Store vectors in Pinecone
        vectors = [(str(i), embedding) for i, embedding in enumerate(embeddings)]
        index.upsert(vectors, namespace="ns1")

if __name__ == "__main__":
    app()
