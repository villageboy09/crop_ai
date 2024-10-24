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
        self.CROPS = {
            "Tomato": {"NPK": "80-40-40", "operations": self.get_monthly_operations("Tomato")},
            "Potato": {"NPK": "100-60-80", "operations": self.get_monthly_operations("Potato")},
            "Corn": {"NPK": "120-60-40", "operations": self.get_monthly_operations("Corn")},
            "Rice": {"NPK": "100-60-40", "operations": self.get_monthly_operations("Rice")},
            "Wheat": {"NPK": "100-50-40", "operations": self.get_monthly_operations("Wheat")},
            "Soybean": {"NPK": "40-20-20", "operations": self.get_monthly_operations("Soybean")},
            "Cotton": {"NPK": "60-40-40", "operations": self.get_monthly_operations("Cotton")},
            "Apple": {"NPK": "100-60-40", "operations": self.get_monthly_operations("Apple")},
            "Grape": {"NPK": "80-40-40", "operations": self.get_monthly_operations("Grape")},
            "Cucumber": {"NPK": "80-40-40", "operations": self.get_monthly_operations("Cucumber")},
        }
        self.VOICES = {
            "English": "en-US-AriaNeural",
            "Hindi": "hi-IN-AditiNeural",
            "Telugu": "te-IN-PriyaNeural"
        }
        self.selected_voice = self.VOICES["English"]  # Default voice

    def get_monthly_operations(self, crop):
        # Define month-specific operations for Kharif and Rabi seasons
        operations = {
            "Kharif": {
                "Tomato": "Sow seeds in June-July; apply NPK as needed.",
                "Potato": "Plant in June; ensure proper irrigation.",
                "Corn": "Plant in June; apply fertilizers as needed.",
                "Rice": "Transplant in July; manage water levels.",
                "Wheat": "Not typically grown in Kharif.",
                "Soybean": "Sow seeds in June; monitor pests.",
                "Cotton": "Plant in June; apply insecticides as needed.",
                "Apple": "Not typically grown in Kharif.",
                "Grape": "Prune in June; ensure good irrigation.",
                "Cucumber": "Sow seeds in June; manage pests."
            },
            "Rabi": {
                "Tomato": "Sow seeds in October-November; monitor for diseases.",
                "Potato": "Plant in October; ensure proper drainage.",
                "Corn": "Not typically grown in Rabi.",
                "Rice": "Not typically grown in Rabi.",
                "Wheat": "Sow seeds in November; apply fertilizers as needed.",
                "Soybean": "Not typically grown in Rabi.",
                "Cotton": "Not typically grown in Rabi.",
                "Apple": "Plant in November; monitor for diseases.",
                "Grape": "Manage irrigation in winter.",
                "Cucumber": "Sow seeds in November; monitor for pests."
            }
        }
        return operations

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

            Format the response in a clear, structured way without hashtags.
            """

            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }

            url = f"{self.API_URL}?key={self.API_KEY}"
            response = requests.post(
                url,
                headers=headers,
                json=payload
            )

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
        communicate = edge_tts.Communicate(text, self.selected_voice)
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

    # Language selection
    language = st.selectbox("Select Language for Text-to-Speech:", list(analyzer.VOICES.keys()))
    analyzer.selected_voice = analyzer.VOICES[language]  # Update selected voice

    # Create a grid layout for crop selection using columns
    cols = st.columns(3)  # 3 columns for the grid
    selected_crop = None

    # Create crop selection buttons in a grid
    for i, crop in enumerate(analyzer.CROPS.keys()):
        col_idx = i % 3
        with cols[col_idx]:
            if st.button(crop, key=f"crop_{i}", use_container_width=True):
                selected_crop = crop

    if selected_crop:
        st.markdown(f"## Analysis for {selected_crop}")

        # Display NPK requirements
        npk_requirements = analyzer.CROPS[selected_crop]["NPK"]
        st.markdown(f"### NPK Requirements per acre: **{npk_requirements} kg**")

        # Season selection
        season = st.selectbox("Select Season:", ["Kharif", "Rabi"])
        monthly_operations = analyzer.CROPS[selected_crop]["operations"][season]
        st.markdown(f"### Month-specific Operations for {season} season: {monthly_operations}")

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
