import streamlit as st
import asyncio
import edge_tts
from datetime import datetime, timedelta
import requests
import os
import base64
from googletrans import Translator
import json

class StreamlitCropDiseaseAnalyzer:
    def __init__(self):
        # Previous initialization code remains the same
        self.API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
        self.API_KEY = st.secrets["gemini"]["api_key"]
        self.WEATHER_API_KEY = st.secrets["visual_crossing"]["api_key"]
        self.VOICES = {
            'Telugu': 'te-IN-ShrutiNeural',
            'English': 'en-US-AriaNeural',
            'Hindi': 'hi-IN-SwaraNeural'
        }
        
        # Rest of the initialization code remains the same...
        self.translator = Translator()

    # All previous methods remain the same until main()...

    async def generate_audio_analysis(self, text, language, crop_name):
        """Generate audio file from analysis text"""
        try:
            output_file = f"{crop_name}_analysis.mp3"
            clean_text = " ".join(word for word in text.split() if not word.startswith("#"))
            communicate = edge_tts.Communicate(clean_text, self.VOICES[language])
            await communicate.save(output_file)
            return output_file
        except Exception as e:
            st.error(f"Error during audio generation: {str(e)}")
            return None

def get_binary_file_downloader_html(bin_file, file_label='File'):
    """Generate a link for downloading a binary file"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">Download {file_label}</a>'
    return href

def main():
    st.set_page_config(page_title="Enhanced Crop Disease Analyzer", page_icon="🌱", layout="wide")
    st.title("🌱 Enhanced Crop Disease Analyzer")

    analyzer = StreamlitCropDiseaseAnalyzer()

    # Sidebar inputs
    selected_language = st.sidebar.selectbox("Select Language", list(analyzer.VOICES.keys()))
    location = st.sidebar.text_input("Enter your location (City, State)", "Delhi, India")
    acres = st.sidebar.number_input("Enter area in acres", min_value=0.1, value=1.0)
    sowing_date = st.sidebar.date_input("Select Sowing Date", datetime.now() - timedelta(days=30))
    
    selected_crop = st.selectbox("Select Crop", list(analyzer.CROPS.keys()))

    if st.button("Analyze Crop"):
        with st.spinner("Analyzing crop and generating audio..."):
            st.markdown(f"## Analysis for {selected_crop}")

            # Weather data
            weather_data = analyzer.get_weather_data(location)
            if weather_data:
                st.markdown(f"### Current Weather in {location}:")
                st.markdown(f"- Temperature: {weather_data['temperature']}°C")
                st.markdown(f"- Humidity: {weather_data['humidity']}%")
                st.markdown(f"- Conditions: {weather_data['conditions']}")

            # Growth stage calculation
            growth_stage = analyzer.calculate_growth_stage(sowing_date, selected_crop)
            st.markdown(f"### Current Growth Stage: {growth_stage}")

            # NPK requirements
            npk_requirements = analyzer.calculate_npk_requirements(selected_crop, location, acres, growth_stage)
            st.markdown(f"### NPK Requirements for {acres} acre(s):")
            st.markdown(f"- Nitrogen (N): {npk_requirements['N']:.2f} kg")
            st.markdown(f"- Phosphorus (P): {npk_requirements['P']:.2f} kg")
            st.markdown(f"- Potassium (K): {npk_requirements['K']:.2f} kg")

            # Weather-based recommendations
            if weather_data:
                recommendations = analyzer.get_weather_based_recommendations(weather_data, selected_crop, growth_stage)
                if recommendations:
                    st.markdown(f"### Weather-Based Recommendations:")
                    for rec in recommendations:
                        st.markdown(f"- {rec}")

            # Crop disease analysis using Gemini API
            st.markdown(f"### Disease Analysis for {selected_crop}:")
            disease_analysis = analyzer.query_gemini_api(selected_crop, selected_language)
            st.markdown(disease_analysis)

            # Automatically generate audio file
            output_file = asyncio.run(analyzer.generate_audio_analysis(
                disease_analysis, 
                selected_language, 
                selected_crop
            ))
            
            if output_file:
                st.success("🔊 Audio analysis has been generated!")
                st.audio(output_file)
                st.markdown("### Download Audio Analysis")
                st.markdown(
                    get_binary_file_downloader_html(output_file, f"{selected_crop} Audio Analysis"), 
                    unsafe_allow_html=True
                )
            else:
                st.error("Failed to generate audio analysis. Please try again.")

if __name__ == "__main__":
    main()
