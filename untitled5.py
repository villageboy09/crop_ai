# -*- coding: utf-8 -*-
import streamlit as st
import asyncio
import edge_tts
from datetime import datetime
import requests
import os
import base64

class StreamlitCropDiseaseAnalyzer:
    def __init__(self):
        # Gemini API Configuration
        self.API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
        self.API_KEY = st.secrets["gemini"]["api_key"]  # Load API key from secrets
        self.VOICE = "en-US-JennyNeural"  # Use a more natural voice model
        self.CROPS = [
            "Tomato", "Potato", "Corn", "Rice", "Wheat",
            "Soybean", "Cotton", "Apple", "Grape", "Cucumber"
        ]

    def query_gemini_api(self, crop):
        """Query Gemini API for crop disease information"""
        try:
            headers = {
                "Content-Type": "application/json"
            }

            prompt = f"""
            Analyze and provide detailed information about common diseases in {crop} cultivation.
            For each disease, include:
            1. Disease name
            2. Symptoms
            3. Favorable conditions
            4. Prevention methods
            5. Treatment options

            Format the response in a clear, structured way.
            """

            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }

            url = f"{self.API_URL}?key={self.API_KEY}"
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                return response.json()["candidates"][0]["content"]["parts"][0]["text"]
            else:
                error_msg = f"Error: API returned status code {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f"\nDetails: {error_detail.get('error', {}).get('message', 'No details available')}"
                except:
                    pass
                return error_msg

        except Exception as e:
            return f"Error querying API: {str(e)}"

    async def text_to_speech(self, text, output_file):
        """Convert text to speech using edge-tts"""
        # Clean the text by removing asterisks
        cleaned_text = text.replace('*', '')  
        communicate = edge_tts.Communicate(cleaned_text, self.VOICE)
        await communicate.save(output_file)

def get_binary_file_downloader_html(bin_file, file_label='File'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">Download {file_label}</a>'
    return href

def main():
    st.set_page_config(
        page_title="Crop Disease Analyzer",
        page_icon="🌱",
        layout="wide"
    )

    st.title("🌱 Crop Disease Analyzer")
    st.markdown("""Select a crop to analyze common diseases and get detailed information including prevention and treatment methods.""")

    analyzer = StreamlitCropDiseaseAnalyzer()

    # Create a grid layout for crop selection using columns
    cols = st.columns(3)  # 3 columns for the grid
    selected_crop = None

    # Create crop selection buttons in a grid
    for i, crop in enumerate(analyzer.CROPS):
        col_idx = i % 3
        with cols[col_idx]:
            if st.button(crop, key=f"crop_{i}", use_container_width=True):
                selected_crop = crop

    if selected_crop:
        st.markdown(f"## Analysis for {selected_crop}")

        # Create a spinner while analyzing
        with st.spinner(f'Analyzing diseases for {selected_crop}...'):
            # Get disease information
            analysis_text = analyzer.query_gemini_api(selected_crop)

            if "Error:" in analysis_text:
                st.error(analysis_text)
            else:
                # Display analysis text
                st.markdown(analysis_text)

                # Generate audio file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                audio_file = f"crop_disease_analysis_{selected_crop.lower()}_{timestamp}.mp3"

                with st.spinner('Generating audio...'):
                    asyncio.run(analyzer.text_to_speech(analysis_text, audio_file))

                # Audio player
                with open(audio_file, 'rb') as audio_data:
                    st.audio(audio_data.read(), format='audio/mp3')

                # Download button
                st.markdown(get_binary_file_downloader_html(audio_file, 'Audio Summary'), unsafe_allow_html=True)

                # Clean up audio file
                try:
                    os.remove(audio_file)
                except:
                    pass

if __name__ == "__main__":
    main()
