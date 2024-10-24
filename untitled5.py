# -*- coding: utf-8 -*-
import streamlit as st
import asyncio
import edge_tts
from datetime import datetime
import requests
import os
import base64
from googletrans import Translator  # Import translator for Hindi translation

class StreamlitCropDiseaseAnalyzer:
    def __init__(self):
        # Gemini API Configuration
        self.API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
        self.API_KEY = st.secrets["gemini"]["api_key"]  # Load API key from secrets
        self.VOICES = {
            'Telugu': 'te-IN-ShrutiNeural',
            'English': 'en-US-AriaNeural',
            'Hindi': 'hi-IN-SwaraNeural'
        }
        self.CROPS = [
            "Tomato", "Potato", "Corn", "Rice", "Wheat",
            "Soybean", "Cotton", "Apple", "Grape", "Cucumber"
        ]
        self.NPK_REQUIREMENTS = {
            "Tomato": {"N": 120, "P": 80, "K": 100},
            "Potato": {"N": 150, "P": 100, "K": 120},
            "Corn": {"N": 200, "P": 50, "K": 100},
            "Rice": {"N": 100, "P": 30, "K": 70},
            "Wheat": {"N": 120, "P": 60, "K": 70},
            "Soybean": {"N": 40, "P": 20, "K": 30},
            "Cotton": {"N": 150, "P": 70, "K": 80},
            "Apple": {"N": 80, "P": 60, "K": 70},
            "Grape": {"N": 100, "P": 40, "K": 50},
            "Cucumber": {"N": 90, "P": 40, "K": 60}
        }
        self.MONTH_SPECIFIC_OPERATIONS = {
            "Kharif": {
                "Tomato": "Transplant in June, harvest in September.",
                "Potato": "Sow in June, harvest in September.",
                # Add other crops and their operations
            },
            "Rabi": {
                "Tomato": "Transplant in December, harvest in March.",
                "Potato": "Sow in November, harvest in February.",
                # Add other crops and their operations
            }
        }
        self.translator = Translator()

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

    async def text_to_speech(self, text, output_file, language):
        """Convert text to speech using edge-tts"""
        voice = self.VOICES[language]
        try:
            # Remove hashtags and unwanted characters from text
            clean_text = " ".join(word for word in text.split() if not word.startswith("#"))
            communicate = edge_tts.Communicate(clean_text, voice)
            await communicate.save(output_file)
        except Exception as e:
            st.error(f"Error during TTS conversion: {str(e)}")
            raise

    def get_npk_requirements(self, crop):
        """Get NPK requirements for a specific crop"""
        return self.NPK_REQUIREMENTS.get(crop, {"N": 0, "P": 0, "K": 0})

    def get_month_specific_operations(self, crop, season):
        """Get month-specific operations for the selected crop and season"""
        return self.MONTH_SPECIFIC_OPERATIONS.get(season, {}).get(crop, "No operations available.")

    def translate_text(self, text, target_language):
        """Translate text to the target language using googletrans"""
        if target_language == 'Hindi':
            translation = self.translator.translate(text, src='en', dest='hi')
            return translation.text
        return text

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
    st.markdown("Analyze common diseases in crops with NPK requirements and operations, available in Telugu, Hindi, and English.")

    analyzer = StreamlitCropDiseaseAnalyzer()

    # Step 1: Language selection
    selected_language = st.selectbox("Select Language", list(analyzer.VOICES.keys()))

    # Step 2: Crop selection
    selected_crop = st.selectbox("Select Crop", analyzer.CROPS)

    # Step 3: Season selection
    selected_season = st.selectbox("Select Season", ["Kharif", "Rabi"])

    if selected_crop:
        st.markdown(f"## Analysis for {selected_crop}")

        # Display NPK requirements
        npk = analyzer.get_npk_requirements(selected_crop)
        st.markdown(f"### NPK Requirements per acre (in kg):")
        st.markdown(f"**Nitrogen (N):** {npk['N']} kg, **Phosphorus (P):** {npk['P']} kg, **Potassium (K):** {npk['K']} kg")

        # Display month-specific operations
        operations = analyzer.get_month_specific_operations(selected_crop, selected_season)
        st.markdown(f"### Month-specific Operations:")
        st.markdown(operations)

        # Create a spinner while analyzing
        with st.spinner(f'Analyzing diseases for {selected_crop} in {selected_language}...'):
            # Get disease information
            analysis_text = analyzer.query_gemini_api(selected_crop)

            if "Error:" in analysis_text:
                st.error(analysis_text)
            else:
                # Translate the analysis text if Hindi is selected
                analysis_text = analyzer.translate_text(analysis_text, selected_language)

                # Display analysis text
                st.markdown(analysis_text)

                # Generate audio file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                audio_file = f"crop_disease_analysis_{selected_crop.lower()}_{timestamp}.mp3"

                with st.spinner('Generating audio...'):
                    asyncio.run(analyzer.text_to_speech(analysis_text, audio_file, selected_language))

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
