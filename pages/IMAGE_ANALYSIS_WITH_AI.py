import streamlit as st
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch
import nest_asyncio
from PIL import Image
import base64
from io import BytesIO
import os
from huggingface_hub import login

# Authenticate with Hugging Face
huggingface_token = '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'
login(huggingface_token)

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Function to encode image in base64
def encode_image(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# Function to analyze image using BLIP
def analyze_image_with_blip(image, prompt):
    model_id = "Salesforce/blip-image-captioning-base"
    dtype = torch.bfloat16
    device = "cuda:0" if torch.cuda.is_available() else "cpu"

    model = BlipForConditionalGeneration.from_pretrained(
        model_id,
        torch_dtype=dtype,
    ).to(device).eval()
    processor = BlipProcessor.from_pretrained(model_id)

    model_inputs = processor(text=prompt, images=image, return_tensors="pt").to(device)
    input_len = model_inputs["input_ids"].shape[-1]

    with torch.inference_mode():
        generation = model.generate(**model_inputs, max_new_tokens=200, do_sample=False)  # Increased max_new_tokens
        generation = generation[0][input_len:]
        decoded = processor.decode(generation, skip_special_tokens=True)
    
    return decoded

def app():
    st.markdown("<div class='centered-logo'>", unsafe_allow_html=True)
    st.image('images/logo_m.jpg', width=200)
    st.markdown("</div>", unsafe_allow_html=True)
    st.title("Image Analysis")
    st.write("This is the Image Analysis page.")
    
    # Image Analysis Section
    st.header("Image Analysis with BLIP")
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    question = st.text_input("Enter your question about the image:")
    
    if uploaded_file is not None and question:
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded Image.', use_column_width=True)
        
        blip_prompt = question  # Use the question as the prompt for BLIP
        blip_response = analyze_image_with_blip(image, blip_prompt)
        st.write("Analysis with BLIP:")
        st.write(blip_response)
    else:
        if not uploaded_file:
            st.warning("Please upload an image.")
        if not question:
            st.warning("Please enter a question about the image.")

if __name__ == "__main__":
    app()
