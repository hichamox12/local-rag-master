import streamlit as st
import PyPDF2
import logging
from langchain_community.embeddings import OpenAIEmbeddings
from pinecone import Pinecone, ServerlessSpec
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)

# Get API keys from environment variables
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")
embeddings = OpenAIEmbeddings(openai_api_key=api_key)

pinecone_api_key = os.getenv("PINECONE_API_KEY")
if not pinecone_api_key:
    raise ValueError("PINECONE_API_KEY not found in environment variables")
pc = Pinecone(api_key=pinecone_api_key)
index_name = "quicksart"

existing_indexes = pc.list_indexes().names()
if index_name not in existing_indexes:
    pc.create_index(
        name=index_name,
        dimension=1536,  
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")  
    )
else:
    logging.info(f"Index '{index_name}' already exists. Using the existing index.")

index = pc.Index(index_name)

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

def split_text_into_chunks(text, num_chunks=3):
    words = text.split()
    total_words = len(words)
    chunk_size = total_words // num_chunks
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 > chunk_size and len(chunks) < num_chunks - 1:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(word)
        current_length += len(word) + 1
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks    

def add_pdf_to_pinecone(pdf_texts):
    chunk_id = 0
    for pdf_index, pdf_text in enumerate(pdf_texts):
        chunks = split_text_into_chunks(pdf_text, num_chunks=3)
        vectors = embeddings.embed_documents(chunks)
        upserts = []
        for i, vector in enumerate(vectors):
            metadata = {"text": chunks[i], "pdf_index": pdf_index, "chunk_index": i}  
            upserts.append((f"pdf-{pdf_index}-chunk-{chunk_id}", vector, metadata))
            chunk_id += 1
        
        try:
            index.upsert(upserts)
            logging.info(f"Upserted {len(upserts)} vectors for PDF {pdf_index}")
        except Exception as e:
            logging.error(f"Error upserting vectors for PDF {pdf_index}: {e}")

def DOCUMENTS_UPLOAD_PAGE():
    st.markdown("<div class='centered-logo'>", unsafe_allow_html=True)
    st.image('images/logo_m.png', width=200)
    st.markdown("</div>", unsafe_allow_html=True)
    st.title("Upload and Embed PDF")

    uploaded_files = st.file_uploader("Upload multiple PDFs (max 200 MB each)", type="pdf", accept_multiple_files=True)

    if uploaded_files:
        all_pdf_texts = []
        for uploaded_file in uploaded_files:
            if uploaded_file.size > 200 * 1024 * 1024:
                st.error(f"File {uploaded_file.name} exceeds the 200 MB size limit.")
                continue

            pdf_text = extract_text_from_pdf(uploaded_file)
            if pdf_text:
                all_pdf_texts.append(pdf_text)
                st.success(f"PDF content from {uploaded_file.name} has been added to the model context and saved.")
                logging.info(f"PDF text from {uploaded_file.name}: {pdf_text}")  
            else:
                st.error(f"Failed to extract text from {uploaded_file.name}.")

        add_pdf_to_pinecone(all_pdf_texts)  
        st.session_state["pdf_text"] = " ".join(all_pdf_texts)  

if __name__ == "__main__":
    DOCUMENTS_UPLOAD_PAGE()
