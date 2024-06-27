import streamlit as st
from pydub import AudioSegment
import os
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from huggingface_hub import login
import numpy as np
import torch

print(torch.__version__)
print(torch.cuda.is_available())

# Set your Hugging Face API token
hf_token = "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"

# Login to Hugging Face
login(hf_token)

# Load the Hugging Face model and processor
model_id = "openai/whisper-large-v3"
device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

model = WhisperForConditionalGeneration.from_pretrained(
    model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_auth_token=hf_token
)
model.to(device)

processor = WhisperProcessor.from_pretrained(model_id, use_auth_token=hf_token)

# Function to transcribe audio using Hugging Face model
def transcribe_audio(file):
    try:
        # Load the audio file using Pydub
        audio = AudioSegment.from_file(file)
        # Ensure the audio is in mono channel and correct sampling rate
        audio = audio.set_frame_rate(16000).set_channels(1)
        # Export as WAV format for the model
        temp_filename = "temp.wav"
        audio.export(temp_filename, format="wav")

        # Read the audio data as numpy array
        audio_data = np.array(audio.get_array_of_samples()).astype(np.float32) / 32768.0

        # Process the audio data with WhisperProcessor
        inputs = processor(audio_data, sampling_rate=16000, return_tensors="pt")
        input_features = inputs.input_features.to(device)

        # Generate transcription
        with torch.no_grad():
            predicted_ids = model.generate(input_features)
        transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        
        os.remove(temp_filename)  # Clean up the temporary file
        return transcription
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

# Streamlit app
def app():
    st.markdown("<div class='centered-logo'>", unsafe_allow_html=True)
    st.image('images/logo_m.jpg', width=200)
    st.markdown("</div>", unsafe_allow_html=True)

    st.title("Audio Whisper")
    st.write("Upload an audio file for transcription:")

    audio_file = st.file_uploader("Upload Audio", type=["wav", "mp3", "m4a"])

    if audio_file is not None:
        st.audio(audio_file, format='audio/wav')
        transcription = transcribe_audio(audio_file)
        st.write("Transcription:")
        st.write(transcription)

if __name__ == "__main__":
    app()
